# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging

from django.utils import dateparse
from workmodel.transitions import TransitionsCollection, Transitions, Transition 
from workmodel.hierarchy import Hierarchy, HierarchyLevel, CustomHierarchyLevel, EpicHierarchyLevel, SubTaskHierarchyLevel
from workmodel.utils import WorkmodelJira

logger = logging.getLogger('workmodel_logger')

class JiraService(object):
    def __init__(self, sc, jira=None, addon_jira=None, account_id=None, *args, **kwargs):
        self.sc = sc
        if jira:
            self.jira = jira
        else:
            self.jira = self._connect_jira(account_id)
        if addon_jira:
            self.addon_jira = addon_jira
        else:
            self.addon_jira = self._connect_jira(False)
        # get current version
        version = self.current_version()
        # get configuration
        conf = None
        for i in range(version, 0, -1):
            conf_call = getattr(self, 'configuration_{}'.format(i), None)
            if conf_call:
                try:
                    conf = conf_call()
                except:
                    continue
        # get version from configuration
        if conf:
            old_version = self.version_from_configuration(conf)
            # apply migrations from configuration version to current version
            for i in range(old_version, version):
                migration_call = getattr(self, 'migrate_from_{}'.format(i), None)
                if migration_call:
                    conf = migration_call(conf)
            self.conf = conf
        else:
            self.conf = self.default_configuration()

    def _connect_jira(self, account_id):
        if not account_id:
            jira = WorkmodelJira(self.sc.host, jwt={'secret': self.sc.shared_secret, 'payload': {'iss': self.sc.key}})
        else:
            token = self.sc.create_user_token(account_id)
            options = {
                'server': self.sc.host,
                'headers': {         
                    'Authorization': 'Bearer {}'.format(token),
                }            
            }
            jira = WorkmodelJira(options=options)
        return jira

    def current_version(self):
        raise NotImplementedError

    def version_from_configuration(self, conf):
        raise NotImplementedError

    def default_configuration(self):
        raise NotImplementedError


class WorkmodelService(JiraService):
    CONFIGURATION_APP_KEY = 'workmodel'
    CONFIGURATION_VERSION = 2

    def __init__(self, sc, *args, **kwargs):
        super(WorkmodelService, self).__init__(sc, *args, **kwargs)
        # instantiate the services
        self.hierarchy = HierarchyService(self.sc, *args, **kwargs)
        self.business_time = BusinessTimeService(self.sc, self.hierarchy, *args, **kwargs)

    def current_version(self):
        return WorkmodelService.CONFIGURATION_VERSION

    def configuration_1(self):
        conf = self.addon_jira.app_property(self.sc.key, "workmodel-configuration")
        return conf

    def configuration_2(self):
        conf = self.addon_jira.app_property(self.sc.key, WorkmodelService.CONFIGURATION_APP_KEY)
        return conf

    def migrate_from_1(self, conf):
        # Save the current configuration into their corresponding services configuration
        hierarchy_conf = {
            'version': 1,
            'hierarchy': conf.raw['value']['hierarchy']
        }
        self.addon_jira.create_app_property(self.sc.key, HierarchyService.CONFIGURATION_APP_KEY, hierarchy_conf)
        business_time_conf = {
            'version': 1,
            'task_id': conf.raw['value']['task_id'],
            'start_field_id': None,
            'end_field_id': None,
        }
        self.addon_jira.create_app_property(self.sc.key, BusinessTimeService.CONFIGURATION_APP_KEY, business_time_conf)
        # Finally remove the old configuration and keep just the version for compatibility reasons
        conf.delete()
        self.addon_jira.create_app_property(self.sc.key, WorkmodelService.CONFIGURATION_APP_KEY, {'version': 2})
        conf = self.addon_jira.app_property(self.sc.key, WorkmodelService.CONFIGURATION_APP_KEY)
        return conf

    def version_from_configuration(self, conf):
        return conf.value.version

    def default_configuration(self):
        self.addon_jira.create_app_property(self.sc.key, WorkmodelService.CONFIGURATION_APP_KEY, {'version': WorkmodelService.CONFIGURATION_VERSION})
        conf = self.addon_jira.app_property(self.sc.key, HierarchyService.CONFIGURATION_APP_KEY)
        return conf

 
class HierarchyService(JiraService):
    CONFIGURATION_APP_KEY = 'workmodel.hierarchy'
    CONFIGURATION_VERSION = 2

    def __init__(self, sc, *args, **kwargs):
        super(HierarchyService, self).__init__(sc, *args, **kwargs)
        self.hierarchies = []
        for h in self.conf.raw['value']['hierarchies']:
            self.hierarchies.append(Hierarchy(self.jira, h['name'], h['levels']))

    def current_version(self):
        return HierarchyService.CONFIGURATION_VERSION

    def configuration_1(self):
        conf = self.addon_jira.app_property(self.sc.key, HierarchyService.CONFIGURATION_APP_KEY)
        return conf

    def migrate_from_1(self, conf):
        raw = conf.raw['value']
        # Make the current hierarchy be a hierarchies[] with a default one
        new_conf = {'version': 2, 'last_id': 1}
        default_hierarchy = {'name': 'Default', 'id': 1, 'levels': raw['hierarchy']}
        new_conf['hierarchies'] = [default_hierarchy]
        self.addon_jira.create_app_property(self.sc.key, HierarchyService.CONFIGURATION_APP_KEY, new_conf)
        conf = self.addon_jira.app_property(self.sc.key, HierarchyService.CONFIGURATION_APP_KEY)
        return conf

    def version_from_configuration(self, conf):
        return conf.value.version

    def default_configuration(self):
        hierarchy_conf = {
            'version': HierarchyService.CONFIGURATION_VERSION,
            'hierarchies': [],
            'last_id': 0,
        }
        self.addon_jira.create_app_property(self.sc.key, HierarchyService.CONFIGURATION_APP_KEY, hierarchy_conf)
        conf = self.addon_jira.app_property(self.sc.key, HierarchyService.CONFIGURATION_APP_KEY)
        return conf

    def child_issues(self, issue, expand=None, extra_jql=None, skip_levels=None, recurse=True):
        # No configuration, do nothing
        if not self.hierarchies:
            raise ValueError

        if not skip_levels:
            already_calculated = []
        else:
            already_calculated = skip_levels
        
        for h in self.hierarchies:
            logger.info("Processing hierarchy {} for {}".format(h.name, issue))
            # No configuration, do nothing
            if not h.hierarchies:
                continue
    
            # A single hierarchy, compare the issuetype only
            issue = self.jira._get_issue(issue)
            if len(h.hierarchies) == 1:
                if h.hierarchies[0].check_issue_type(issue):
                    if h.hierarchies[0] not in already_calculated:
                        yield issue
                else:
                    continue
            # TODO reverse on the configuration
            for idx in range(0, len(h.hierarchies) - 1):
                l = h.hierarchies[idx]
                l_prev = h.hierarchies[idx+1]
                if l.check_issue_type(issue):
                    logger.debug("Found hierarchy level {}".format(l))
                    if l in already_calculated:
                        logger.debug("Hierarchy {} already processed, skipping it".format(l))
                        break
                    already_calculated.append(l)
                    jql = l.children_jql(issue, l_prev)
                    if l_prev.is_operative and extra_jql:
                        jql = "({0}) {1}".format(jql, extra_jql)
                    children = self.jira.search_issues_gen(jql, expand)
                    has_children = False
                    for ch in children:
                        has_children = True
                        if (extra_jql and l_prev.is_operative) or not extra_jql:
                            yield ch
                        if recurse:
                            for sch in self.child_issues(ch, expand=expand, extra_jql=extra_jql, skip_levels=already_calculated, recurse=recurse):
                                yield sch
                    # no issues, try with the next level
                    if not has_children:
                        continue
                    break

class BusinessTimeService(JiraService):
    CONFIGURATION_APP_KEY = 'workmodel.business_time'
    CONFIGURATION_VERSION = 1

    def __init__(self, sc, hierarchy, *args, **kwargs):
        super(BusinessTimeService, self).__init__(sc, *args, **kwargs)
        self.hierarchy = hierarchy
        self.statuses = self.jira.statuses()

    def current_version(self):
        return BusinessTimeService.CONFIGURATION_VERSION

    def configuration_1(self):
        conf = self.addon_jira.app_property(self.sc.key, BusinessTimeService.CONFIGURATION_APP_KEY)
        return conf

    def version_from_configuration(self, conf):
        return conf.value.version

    def default_configuration(self):
        business_time_conf = {
            'version': BusinessTimeService.CONFIGURATION_VERSION,
            'task_id': None,
            'start_field_id': None,
            'end_field_id': None,
        }
        self.addon_jira.create_app_property(self.sc.key, BusinessTimeService.CONFIGURATION_APP_KEY, business_time_conf)
        conf = self.addon_jira.app_property(self.sc.key, BusinessTimeService.CONFIGURATION_APP_KEY)
        return conf

    def transition_to_days(self, from_transition, to_transition):
        fromDate = from_transition['created']
        toDate = to_transition['created']
        # Get the timespan
        daygenerator = (fromDate + datetime.timedelta(x + 1) for x in range((toDate - fromDate).days))
        # Remove non working days
        days = sum(1 for day in daygenerator if day.weekday() < 5)
        return days

    def generate_transition_categories(self, issue):
        transitions = Transitions()
        # get the transitions
        abs_start = datetime.date.max
        next_status = None
        next_start = None
        for h in issue.changelog.histories:
            created = dateparse.parse_datetime(h.created).date()
            if created < abs_start:
                abs_start = created
    
            for item in h.items:
                if item.field != 'status':
                    continue
  
                fromStatusList = [x for x in self.statuses if x.id == getattr(item, 'from')]
                toStatusList = [x for x in self.statuses if x.id == getattr(item, 'to')]
                # Try by name
                if not fromStatusList:
                    fromStatusList = [x for x in self.statuses if x.name == item.fromString]
                if not toStatusList:
                    toStatusList = [x for x in self.statuses if x.name == item.toString]
                try:
                    fromStatus = fromStatusList[0]
                    toStatus = toStatusList[0]
                except IndexError:
                    logger.error("Status id: {} name: {} does not exist for issue {}".format(getattr(item, 'from'), item.fromString, issue))
                    continue
    
                # We have a status category change
                if fromStatus.statusCategory.name != toStatus.statusCategory.name:
                    start = created
                    if not next_status:
                        end = datetime.date.today()
                    else:
                        end = next_start
                    diff = end - start
                    if diff.days != 0:
                        t = Transition(start, end, toStatus.statusCategory.name)
                        transitions.append(t)
                    next_status = fromStatus
                    next_start = created
        # Create the very first transition
        if transitions:
            last = transitions[len(transitions) - 1]
            diff = last.from_date - abs_start
            if diff.days != 0:
                if fromStatus.statusCategory.name != last.status:
                    t = Transition(abs_start, last.from_date, fromStatus.statusCategory.name)
                    transitions.append(t)
                else:
                    last.from_date = abs_start
        else:
            start = dateparse.parse_datetime(issue.fields.created).date()
            end = datetime.date.today()
            diff = end - start
            if diff.days != 0:
                t = Transition(start, end, issue.fields.status.statusCategory.name)
                transitions.append(t)
        # Join transitions less than one day
        return transitions

    def business_time(self, issue):
        logger.info("Updating issue {} business time".format(issue))
        issue = self.jira._get_issue(issue, expand='changelog')

        # Only calculate once for each hierarchy level
        already_calculated = []

        # The result
        transitions = Transitions()

        has_children = False
        all_transitions = TransitionsCollection()
        # Get the hierarchy level this issue belongs to
        for h in self.hierarchy.hierarchies:
            logger.info("Processing hierarchy {}".format(h.name))
            # In case the hierarchy level was already calculated, there's nothing
            # to do
            l = h.hierarchy_level(issue)
            if not l:
                logger.info("No level found, nothing to do")
                continue
            if l in already_calculated:
                logger.info("Level {} already calculated, nothing to do".format(l))
                continue
            else:
                already_calculated.append(l)
            
            logger.info("Level wasn't calculated, doing so")
            # Check if it is a container or an operative issue
            # Given that the child_issues() method is already recursive
            # avoid calling it again in case another matching hierarchy
            # level is a container
            if l.is_container and not has_children:
                # Get the children issue
                children = self.hierarchy.child_issues(issue, expand='changelog', recurse=False)
                for ch in children:
                    has_children = True
                    all_transitions.append(self.business_time(ch))
            if not has_children and l.is_operative:
                # No children, do our own stuff
                operative_transition = self.generate_transition_categories(issue)
                all_transitions.append(operative_transition)

        if len(all_transitions):
            logger.info("Normalizing {} transitions for issue {}: {}".format(len(all_transitions), issue, all_transitions))
            # Fake transitions
            normalized = all_transitions.normalize()
            # Bool them all
            transposed = normalized.transpose()
            intersection = transposed.intersect()
            # Merge common transitions
            transitions = intersection.merge()

        # Store the information as a property
        statuses = [{'from_date': str(t.from_date), 'to_date': str(t.to_date), 'status': t.status} for t in transitions]
        days = sum(t.to_days() for t in transitions if t.status == Transition.IN_PROGRESS)
        logger.info("Days in progress for {} is {}".format(issue, days))     

        self.jira.add_issue_property(issue.key, "transitions",
            { 'progress_summation': days, 'statuses': statuses }
        )
        return transitions


    def update_in_progress_business_time(self):
        logger.info("Updating all In-Progress issues")
        # Get all the operative hierarchies
        issue_types = []
        for h in self.hierarchy.hierarchies:
            for l in h.hierarchies:
                if l.is_operative:
                    issue_types += l.get_issue_types()
        # Uniquify the list
        issue_types = list(set(issue_types))
        if not issue_types:
            logger.info("No issue types set, nothing to do")
            return

        # Search issues whoes current statusCategory is In Progress
        issues = self.jira.search_issues_gen("statusCategory = 'In Progress' AND type IN ({})".format(",".join("'{0}'".format(it) for it in issue_types)))
        to_update = []
        for i in issues:
            for h in self.hierarchy.hierarchies:
                try:
                    root = h.root_issue(i.key)
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
        conf = self.conf.raw['value']
        conf['task_id'] = task_id
        self.conf.update(conf)

        issues = self.jira.search_issues_gen("", expand='changelog')
        for issue in issues:
            self.business_time(issue)
        # Remove the addon task id
        conf = self.conf.raw['value']
        conf['task_id'] = None
        self.conf.update(conf)
