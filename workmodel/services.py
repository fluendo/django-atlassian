# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import jira
import logging
from jira import JIRA

from django.utils import dateparse

logger = logging.getLogger('workmodel_logger')

class WorkmodelService(object):
    def __init__(self, sc, conf=None):
        self.sc = sc
        self.jira = JIRA(self.sc.host, jwt={'secret': self.sc.shared_secret, 'payload': {'iss': self.sc.key}})
        if not conf:
            conf = self.get_configuration()
        # instantiate the services
        self.hierarchy = HierarchyService(self.sc, self.jira, conf['hierarchy'])
        self.business_time = BusinessTimeService(self.sc, self.jira, conf, self.hierarchy)

        # Create the app configuration in case it is not there yet
        self.jira.create_app_property(sc.key, 'workmodel-configuration', conf)

    def get_configuration(self):
        # already created configuration
        conf = {
            'hierarchy': [],
            'task_id': None,
            'version': 1,
        }
        try:
            props = self.jira.app_properties(self.sc.key)
            for p in props:
                if p.key == 'workmodel-configuration':
                    if hasattr(p.value, 'task_id'):
                        conf['task_id'] = p.value.task_id
                    else:
                        conf['task_id'] = None
                    if hasattr(p.value, 'hierarchy'):
                        conf['hierarchy'] = p.raw['value']['hierarchy']
                    else:
                        conf['hierarchy'] = []
                    if hasattr(p.value, 'version'):
                        conf['version'] = p.value.version
                    else:
                        conf['version'] = 1
        except:
            pass
        return conf


class JiraService(object):
    def __init__(self, sc, jira, *args, **kwargs):
        self.sc = sc
        self.jira = jira

    def _get_issue(self, issue, expand=None):
        if type(issue) == str or type(issue) == unicode:
            return self.jira.issue(issue, expand=expand)
        elif type(issue) == jira.resources.Issue:
            return issue
        else:
            raise ValueError

    def search_issues(self, jql, expand=None):
        start_at = 0
        result = []

        r = self.jira.search_issues(jql, startAt=start_at, expand=expand)
        total = len(r)
        while total != 0:
            for i in r:
                yield i
            start_at += total
            r = self.jira.search_issues(jql, startAt=start_at, expand=expand)
            total = len(r)

    def get_default_configuration(self):
        raise NotImplementedError

    
class HierarchyService(JiraService):
    def __init__(self, sc, jira, conf, *args, **kwargs):
        super(HierarchyService, self).__init__(sc, jira, args, kwargs)
        self.hierarchies = []
        if conf:
            for c in conf:
                if c['type'] == 'sub-task':
                    self.hierarchies.append(SubTaskHierarchyLevel(self.jira))
                if c['type'] == 'epic':
                    self.hierarchies.append(EpicHierarchyLevel(self.jira, c['is_operative']))
                elif c['type'] == 'custom':
                    self.hierarchies.append(CustomHierarchyLevel(self.jira, c['is_operative'], c['is_container'], c['issues'], c['field'], c['link']))

    def root_issue(self, issue):
        # No configuration, do nothing
        if not self.hierarchies:
            raise ValueError

        # A single hierarchy, compare the issuetype only
        issue = self._get_issue(issue)
        if len(self.hierarchies) == 1:
            if self.hierarchies[0].check_issue_type(issue):
                return issue
            else:
                raise ValueError
        # Now the complex part, take into account the field and the upper hierarchy
        # Iterate over the list of hierarchies
        # TODO reverse on the configuration
        l = len(self.hierarchies)
        found = False
        for idx in range(1, len(self.hierarchies)):
            idx = l - idx
            h = self.hierarchies[idx]
            h_next = self.hierarchies[idx-1]
            parent = h.parent(issue, h_next)
            if parent:
                issue = parent
                found = True
            else:
                if found:
                    break
                else:
                    continue
        return issue


    def child_issues(self, issue, expand=None, extra_jql=None):
        # No configuration, do nothing
        if not self.hierarchies:
            raise ValueError

        # A single hierarchy, compare the issuetype only
        issue = self._get_issue(issue)
        if len(self.hierarchies) == 1:
            if self.hierarchies[0].check_issue_type(issue):
                yield issue
            else:
                raise ValueError
        # TODO reverse on the configuration
        for idx in range(0, len(self.hierarchies) - 1):
            h = self.hierarchies[idx]
            h_prev = self.hierarchies[idx+1]
            if h.check_issue_type(issue):
                jql = h.children_jql(issue, h_prev)
                if extra_jql:
                    jql = "({0}) {1}".format(jql, extra_jql)
                children = self.search_issues(jql, expand)
                has_children = False
                for ch in children:
                    has_children = True
                    yield ch
                    for sch in self.child_issues(ch, expand=expand, extra_jql=extra_jql):
                        yield sch
                # no issues, try with the next level
                if not has_children:
                    continue
                break

    def hierarchy_level(self, issue):
        # No configuration, do nothing
        if not self.hierarchies:
            raise ValueError

        # A single hierarchy, compare the issuetype only
        issue = self._get_issue(issue)
        if len(self.hierarchies) == 1:
            if self.hierarchies[0].check_issue_type(i):
                return i
            else:
                raise ValueError
        # TODO reverse on the configuration
        ret = None
        for idx in range(0, len(self.hierarchies) - 1):
            h = self.hierarchies[idx]
            h_prev = self.hierarchies[idx+1]
            if h.check_issue_type(issue):
                jql = h.children_jql(issue, h_prev)
                if not jql:
                    continue

                ret = h
                children = self.search_issues(jql)
                # no issues, try with the next level
                if next(children, None) == None:
                    continue
                else:
                    break
        return h

class HierarchyLevel(object):
    def __init__(self, jira, t, is_operative, is_container, *args, **kwargs):
        self.jira = jira
        self.type = t
        self.is_operative = is_operative
        self.is_container = is_container

    def get_issue_types(self):
        raise NotImplementedError

    def parent_upwards_for_issue(self, issue):
        raise NotImplementedError

    def parent_downwards_for_issue(self, issue):
        raise NotImplementedError

    def is_operative(self):
        return self.is_operative

    def is_container(self):
        return self.is_container

    def children_jql_upward(self):
        raise NotImplementedError

    def children_jql_downward(self):
        raise NotImplementedError

    def check_issue_type(self, issue):
        if issue.fields.issuetype.name in self.get_issue_types():
            return True
        else:
            return False

    def parent(self, issue, h_next):
        try:
            parent = self.parent_upwards(issue, h_next)
        except NotImplementedError:
            parent = None
        if not parent:
            try:
                parent = h_next.parent_downwards(issue, self)
            except NotImplementedError:
                parent = None
        return parent

    def children_jql(self, issue, h_prev):
        jql = None
        try:
            jql = self.children_jql_downward().format(issue_key=issue.key)
        except NotImplementedError:
            # go with the next hierarchy level
            try:
                jql = h_prev.children_jql_upward().format(issue_key=issue.key)
            except NotImplementedError:
                pass
        return jql

    def parent_upwards(self, issue, h_next):
        if not self.check_issue_type(issue):
            return None

        issue = self.parent_upwards_for_issue(issue)
        # Check that the parent matches the other hierarchy issue type
        if issue and h_next.check_issue_type(issue):
            return issue
        return None

    def parent_downwards(self, issue, h_prev):
        if not h_prev.check_issue_type(issue):
            return False

        issue = self.parent_downwards_for_issue(issue)
        # Check that the current hierarchy matches the issue type
        if issue and self.check_issue_type(issue):
            return issue
        return None


class SubTaskHierarchyLevel(HierarchyLevel):
    def __init__(self, jira, *args, **kwargs):
        super(SubTaskHierarchyLevel, self).__init__(jira, 'sub-task', True, False, *args, **kwargs)
        self.sub_tasks = list(set([x.name for x in self.jira.issue_types() if x.subtask == True]))
        self.parent_field = [x for x in self.jira.fields() if 'Parent' == x['name']][0]['key']

    def get_issue_types(self):
        return self.sub_tasks

    def parent_upwards_for_issue(self, issue):
        # Get the parent issue
        if not hasattr(issue.fields, self.parent_field):
            return None

        parent_issue = getattr(issue.fields, self.parent_field)
        # The parent issue does not have every field, we need to fetch again
        return self.jira.issue(parent_issue.key)

    def children_jql_upward(self):
        return "parent = {issue_key}"


class EpicHierarchyLevel(HierarchyLevel):
    def __init__(self, jira, is_operative, *args, **kwargs):
        super(EpicHierarchyLevel, self).__init__(jira, 'epic', is_operative, True, *args, **kwargs)
        self.epic = [x.name for x in self.jira.issue_types() if x.name == 'Epic']
        self.epic_field = [x for x in self.jira.fields() if 'Epic Link' == x['name']][0]['key']

    def get_issue_types(self):
        return self.epic

    def parent_downwards_for_issue(self, issue):
        epic_key = getattr(issue.fields, self.epic_field)
        if epic_key:
            return self.jira.issue(epic_key)
        else:
            return None

    def children_jql_downward(self):
        return "'Epic Link' = {issue_key}"


class CustomHierarchyLevel(HierarchyLevel):
    def __init__(self, jira, is_operative, is_container, issues = None, field = None, link = None, *args, **kwargs):
        super(CustomHierarchyLevel, self).__init__(jira, 'custom', is_operative, is_container, *args, **kwargs)
        if issues:
            self.issues = [x.name for x in self.jira.issue_types() if x.id in issues]
        else:
            self.issues = [x.name for x in self.jira.issue_types()]
        self.field = None
        if field:
            self.field = [x for x in self.jira.fields() if x['id'] == field][0]['key']
        self.link = None
        if link:
            self.link = [x for x in self.jira.issue_link_types() if x.id == link][0]

    def get_issue_types(self):
        return self.issues

    def parent_downwards_for_issue(self, issue):
        # We use the upward link to go down
        if self.link:
            for il in issue.fields.issuelinks:
                if il.type.id == self.link.id:
                    if hasattr(il, "inwardIssue"):
                        return self.jira.issue(il.inwardIssue.key)
            return None
        else:
            raise NotImplementedError

    def parent_upwards_for_issue(self, issue):
        # We use the field on the children to go up in the hierarchy
        if self.field:
            if hasattr(issue.fields, self.field):
                field_key = getattr(issue.fields, self.field)
                if field_key:
                    return self.jira.issue(field_key)
            return None
        # We use the inward link to go up
        elif self.link:
            for il in issue.fields.issuelinks:
                if il.type.id == self.link.id:
                    if hasattr(il, "outwardIssue"):
                        return self.jira.issue(il.outwardIssue.key)
            return None
        else:
            raise NotImplementedError

    def children_jql_downward(self):
        if self.field:
            return "{} = {{issue_key}}".format(self.field)
        elif self.link:
            return "issue in linkedIssues({{issue_key}}, {})".format(self.link.outward)
        else:
            raise NotImplementedError


class BusinessTimeService(JiraService):
    def __init__(self, sc, jira, conf, hierarchy, *args, **kwargs):
        super(BusinessTimeService, self).__init__(sc, jira, args, kwargs)
        self.hierarchy = hierarchy
        self.statuses = self.jira.statuses()

    def transition_to_days(self, from_transition, to_transition):
        fromDate = from_transition['created']
        toDate = to_transition['created']
        # Get the timespan
        daygenerator = (fromDate + datetime.timedelta(x + 1) for x in range((toDate - fromDate).days))
        # Remove non working days
        days = sum(1 for day in daygenerator if day.weekday() < 5)
        return days

    def calculate_issue_business_time(self, issue):
        transitions = []
        for h in issue.changelog.histories:
            # Get all transitions
            created = dateparse.parse_datetime(h.created).date()
            for item in h.items:
                if item.field == 'status':
                    # Get transitions where the from status is of "In Progress" category
                    # Get transitions where the to status is of "In Progress" category
                    # Warning: We have duplicate names for statuses
                    fromCategory = toCategory = None
                    for s in self.statuses:
                        if fromCategory and toCategory:
                            break
                        if s.name == item.fromString:
                            fromCategory = s.statusCategory.name
                        if s.name == item.toString:
                            toCategory = s.statusCategory.name
                    if fromCategory != 'In Progress' and toCategory != 'In Progress':
                        continue
                    # Always keep it sorted from oldest to newer
                    transitions.insert(0, {'created': created, 'fromCategory': fromCategory, 'toCategory': toCategory})
        if not transitions:
            days = 0
        else:
            days = 1
            # In case the task is currently in progress, create a fake transition
            if transitions[len(transitions) - 1]['toCategory'] == 'In Progress':
                transitions.append({'created': datetime.date.today(), 'fromCategory': 'In Progress', 'toCategory': 'Done'})
            for i in range(1, len(transitions)):
                # Skip transitions that happened in the same day
                if transitions[i-1]['created'] == transitions[i]['created']:
                    continue
                # Sum every filtered timespan
                days += self.transition_to_days(transitions[i-1], transitions[i])
        return days

    def business_time(self, issue):
        logger.info("Updating issue {} business time".format(issue))
        issue = self._get_issue(issue, expand='changelog')
        # Get the hierarchy level this issue belongs to
        h = self.hierarchy.hierarchy_level(issue)
        # Check if it is a container or an operative issue
        has_children = False
        days = 0
        if h.is_container:
            # Get the children issue
            children = self.hierarchy.child_issues(issue, expand='changelog')
            for ch in children:
                has_children = True
                days += self.business_time(ch)
        if not has_children and h.is_operative:
            # No children, do our own stuff
            days = self.calculate_issue_business_time(issue)
        # Store the information as a property
        logger.info("Days for {} is {}".format(issue, days))     
        self.jira.add_issue_property(issue.key, "transitions", { 'progress_summation': days })
        return days

    def update_in_progress_business_time(self):
        logger.info("Updating all In-Progress issues")
        # Get all the operative hierarchies
        issue_types = []
        for h in self.hierarchy.hierarchies:
            if h.is_operative:
                issue_types += h.get_issue_types()
        # Uniquify the list
        issue_types = list(set(issue_types))
        if not issue_types:
            logger.info("No issue types set, nothing to do")
            return

        # Search issues whoes current statusCategory is In Progress
        issues = self.jira.search_issues("statusCategory = 'In Progress' AND type IN ({})".format(",".join("'{0}'".format(it) for it in issue_types)))
        to_update = []
        for i in issues:
            try:
                root = self.hierarchy.root_issue(i.key)
            except:
                # nothing to do
                continue
            to_update.append(root.key)
        # Uniquify the list
        to_update = list(set(to_update))
        for u in to_update:
            logger.info("Updating business time for In-Progress issue {}".format(u))
            self.business_time(u)

    def update_all_business_time(self, task_id):
        logger.info("Updating all issues")

        # We assume there is already a configuration stored
        prop = None
        props = self.jira.app_properties(self.sc.key)
        for p in props:
            if p.key == 'workmodel-configuration':
                prop = p
                break
        prop.raw['value']['task_id'] = task_id
        prop.update(prop.raw['value'])
        issues = self.search_issues("", expand='changelog')
        for issue in issues:
            self.business_time(issue)
        # Remove the addon task id
        prop = None
        props = self.jira.app_properties(self.sc.key)
        for p in props:
            if p.key == 'workmodel-configuration':
                prop = p
                break
        prop.raw['value']['task_id'] = None
        prop.update(prop.raw['value'])
