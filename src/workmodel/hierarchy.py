# -*- coding: utf-8 -*-
from __future__ import unicode_literals

class Hierarchy(object):
    def __init__(self, jira, name, levels):
        self.hierarchies = []
        self.name = name
        self.jira = jira
        for l in levels:
            if l['type'] == 'sub-task':
                self.hierarchies.append(SubTaskHierarchyLevel(jira))
            if l['type'] == 'epic':
                self.hierarchies.append(EpicHierarchyLevel(jira, l['is_operative']))
            elif l['type'] == 'custom':
                self.hierarchies.append(CustomHierarchyLevel(jira, l['is_operative'], l['is_container'], l['issues'], l['field'], l['link']))

    def root_issue(self, issue):
        # No configuration, do nothing
        if not self.hierarchies:
            raise ValueError

        # A single hierarchy, compare the issuetype only
        issue = self.jira._get_issue(issue)
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

    def child_issues(self, issue, expand=None, extra_jql=None, recurse=True):
        # No configuration, do nothing
        if not self.hierarchies:
            raise ValueError

        # A single hierarchy, compare the issuetype only
        issue = self.jira._get_issue(issue)
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
                if h_prev.is_operative and extra_jql:
                    jql = "({0}) {1}".format(jql, extra_jql)
                children = self.jira.search_issues_gen(jql, expand)
                has_children = False
                for ch in children:
                    has_children = True
                    if (extra_jql and h_prev.is_operative) or not extra_jql:
                        yield ch
                    if recurse:
                        for sch in self.child_issues(ch, expand=expand, extra_jql=extra_jql):
                            yield sch
                # no issues, try with the next level
                if not has_children:
                    continue
                break


    def hierarchy_level(self, issue):
        # No configuration, do nothing
        if not self.hierarchies:
            return None

        # A single hierarchy, compare the issuetype only
        issue = self.jira._get_issue(issue)
        if len(self.hierarchies) == 1:
            if self.hierarchies[0].check_issue_type(i):
                return i
        # TODO reverse on the configuration
        ret = None
        for idx in range(0, len(self.hierarchies)):
            h = self.hierarchies[idx]
            h_prev = None if idx == len(self.hierarchies) - 1 else self.hierarchies[idx+1]
            if h.check_issue_type(issue):
                ret = h

                # No lower hierarchy level, no children to continue
                if not h_prev:
                    continue

                jql = h.children_jql(issue, h_prev)
                if not jql:
                    continue

                children = self.jira.search_issues_gen(jql)
                # no issues, try with the next level
                if next(children, None) == None:
                    continue
                else:
                    break
        return ret

class HierarchyLevel(object):
    def __init__(self, jira, t, is_operative, is_container, *args, **kwargs):
        self.jira = jira
        self.type = t
        self.is_operative = is_operative
        self.is_container = is_container

    def __eq__(self, other):
        if self.type == other.type and self.is_operative == other.is_operative and self.is_container == other.is_container:
            return True
        else:
            return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)

    def get_issue_types(self):
        raise NotImplementedError

    def parent_upwards_for_issue(self, issue):
        raise NotImplementedError

    def parent_downwards_for_issue(self, issue):
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

    def __str__(self):
        return "type: {}, is_container: {}, is_operative: {}".format(self.type, self.is_container, self.is_operative)

    def __repr__(self):
        return str(self)


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

    def __eq__(self, other):
        if super(CustomHierarchyLevel, self).__eq__(other) == False:
            return False
        # Same type, compare in depth
        if self.issues == other.issues and self.field == other.field and self.link == other.link:
            return True
        else:
            return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)

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


