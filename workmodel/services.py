# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import jira
from jira import JIRA

class WorkmodelService(object):
    def __init__(self, sc):
        self.jira = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
        # TODO Handle the configuration


class JiraService(object):
    def __init__(self, sc, *args, **kwargs):
        self.jira = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})

    def _get_issue(self, issue):
        if type(issue) == str:
            return self.jira.issue(issue)
        elif type(issue) == jira.resources.Issue:
            return issue
        else:
            raise ValueError

    def search_issues(self, jql, expand=None):
        start_at = 0
        result = []
        while True:
            r = self.jira.search_issues(jql, startAt=start_at, expand=expand)
            total = len(r)
            if total == 0:
                break
            result += r
            start_at += total
    
        return result

    
class HierarchyService(JiraService):
    def __init__(self, sc, conf, *args, **kwargs):
        super(HierarchyService, self).__init__(sc, args, kwargs)
        self.hierarchies = []
        for c in conf:
            if c['type'] == 'sub-task':
                self.hierarchies.append(SubTaskHierarchyLevel(self.jira))
            if c['type'] == 'epic':
                self.hierarchies.append(EpicHierarchyLevel(self.jira))
            elif c['type'] == 'custom':
                self.hierarchies.append(CustomHierarchyLevel(self.jira, c['issues'], c['field'], c['link']))

    def root_issue(self, issue):
        # No configuration, do nothing
        if not self.hierarchies:
            raise ValueError

        # A single hierarchy, compare the issuetype only
        i = self._get_issue(issue)
        if len(self.hierarchies) == 1:
            if self.hierarchies[0].check_issue_type(i):
                return i
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
            parent = h.parent(i, h_next)
            if parent:
                i = parent
                found = True
            else:
                if found:
                    break
                else:
                    continue
        return i


    def child_issues(self, issue, expand=None):
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
        issues = []
        for idx in range(0, len(self.hierarchies) - 1):
            h = self.hierarchies[idx]
            h_prev = self.hierarchies[idx+1]
            if h.check_issue_type(issue):
                jql = h.children_jql(issue, h_prev)
                children = self.search_issues(jql, expand)
                # no issues, try with the next level
                if not children:
                    continue
                issues += children
                for ch in children:
                    issues += self.child_issues(ch, expand=expand)
                break
        return issues
            

class HierarchyLevel(object):
    def __init__(self, jira, t, *args, **kwargs):
        self.jira = jira
        self.type = t

    def get_issue_types(self):
        raise NotImplementedError

    def parent_upwards_for_issue(self, issue):
        raise NotImplementedError

    def parent_downwards_for_issue(self, issue):
        raise NotImplementedError

    def is_operative(self):
        raise NotImplementedError

    def is_container(self):
        raise NotImplementedError

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
        issues = []
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
        super(SubTaskHierarchyLevel, self).__init__(jira, 'sub-task', *args, **kwargs)
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

    def is_operative(self):
        return True

    def is_container(self):
        return False

    def children_jql_upward(self):
        return "parent = {issue_key}"


class EpicHierarchyLevel(HierarchyLevel):
    def __init__(self, jira, *args, **kwargs):
        super(EpicHierarchyLevel, self).__init__(jira, 'epic', *args, **kwargs)
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

    def is_operative(self):
        return False

    def is_container(self):
        return True

    def children_jql_downward(self):
        return "'Epic Link' = {issue_key}"


class CustomHierarchyLevel(HierarchyLevel):
    def __init__(self, jira, issues = None, field = None, link= None, *args, **kwargs):
        super(CustomHierarchyLevel, self).__init__(jira, 'custom', *args, **kwargs)
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

    def is_operative(self):
        # TODO
        raise NotImplementedError

    def is_container(self):
        # TODO
        raise NotImplementedError

    def children_jql_downward(self):
        if self.field:
            return "{} = {{issue_key}}".format(self.field)
        elif self.link:
            return "issue in linkedIssues({{issue_key}}, {})".format(self.link.outward)
        else:
            raise NotImplementedError


