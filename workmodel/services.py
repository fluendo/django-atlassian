# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from jira import JIRA

class HierarchyService(object):
    def __init__(self, sc, conf, *args, **kwargs):
        self.jira = JIRA(sc.host, jwt={'secret': sc.shared_secret, 'payload': {'iss': sc.key}})
        self.hierarchies = []
        for c in conf:
            if c['type'] == 'sub-task':
                self.hierarchies.append(SubTaskHierarchyLevel(self.jira))
            if c['type'] == 'epic':
                self.hierarchies.append(EpicHierarchyLevel(self.jira))
            elif c['type'] == 'custom':
                self.hierarchies.append(CustomHierarchyLevel(self.jira, c['issues'], c['field'], c['link']))

    def get_root_issue(self, issue_key):
        # No configuration, do nothing
        if not self.hierarchies:
            raise ValueError

        # A single hierarchy, compare the issuetype only
        i = self.jira.issue(issue_key)
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
            parent = h.get_parent(i, h_next)
            if parent:
                i = parent
                found = True
            else:
                if found:
                    break
                else:
                    continue
        return i


class HierarchyLevel(object):
    def __init__(self, jira, t, *args, **kwargs):
        self.jira = jira
        self.type = t

    def get_issue_types(self):
        raise NotImplementedError

    def check_issue_type(self, issue):
        if issue.fields.issuetype.name in self.get_issue_types():
            return True
        else:
            return False

    def get_hierarchy_up_issue(self, issue):
        raise NotImplementedError

    def get_hierarchy_down_issue(self, issue):
        raise NotImplementedError

    def get_parent(self, issue, h_next):
        try:
            parent = self.get_hierarchy_up(issue, h_next)
        except NotImplementedError:
            parent = None
        if not parent:
            try:
                parent = h_next.get_hierarchy_down(issue, self)
            except NotImplementedError:
                parent = None
        return parent

    def get_hierarchy_up(self, issue, h_next):
        if not self.check_issue_type(issue):
            return None

        issue = self.get_hierarchy_up_issue(issue)
        # Check that the parent matches the other hierarchy issue type
        if issue and h_next.check_issue_type(issue):
            return issue
        return None

    def get_hierarchy_down(self, issue, h_prev):
        if not h_prev.check_issue_type(issue):
            return False

        issue = self.get_hierarchy_down_issue(issue)
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

    def get_hierarchy_up_issue(self, issue):
        # Get the parent issue
        if not hasattr(issue.fields, self.parent_field):
            return None

        parent_issue = getattr(issue.fields, self.parent_field)
        # The parent issue does not have every field, we need to fetch again
        return self.jira.issue(parent_issue.key)


class EpicHierarchyLevel(HierarchyLevel):
    def __init__(self, jira, *args, **kwargs):
        super(EpicHierarchyLevel, self).__init__(jira, 'epic', *args, **kwargs)
        self.epic = [x.name for x in self.jira.issue_types() if x.name == 'Epic']
        self.epic_field = [x for x in self.jira.fields() if 'Epic Link' == x['name']][0]['key']

    def get_issue_types(self):
        return self.epic

    def get_hierarchy_down_issue(self, issue):
        epic_key = getattr(issue.fields, self.epic_field)
        if epic_key:
            return self.jira.issue(epic_key)
        else:
            return None


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

    def get_hierarchy_down_issue(self, issue):
        # We use the upward link to go down
        if self.link:
            for il in issue.fields.issuelinks:
                if il.type.id == self.link.id:
                    if hasattr(il, "inwardIssue"):
                        return self.jira.issue(il.inwardIssue.key)
            return None
        else:
            raise NotImplementedError

    def get_hierarchy_up_issue(self, issue):
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
