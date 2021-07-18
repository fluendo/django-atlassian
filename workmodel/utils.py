# -*- coding: utf-8 -*-
import jira
from jira import JIRA

class WorkmodelJira(JIRA):
    def _get_issue(self, issue, expand=None):
        if type(issue) == str or type(issue) == unicode:
            return self.issue(issue, expand=expand)
        elif type(issue) == jira.resources.Issue:
            return issue
        else:
            raise ValueError

    def search_issues_gen(self, jql, expand=None):
        start_at = 0
        result = []

        r = self.search_issues(jql, startAt=start_at, expand=expand)
        total = len(r)
        while total != 0:
            for i in r:
                yield i
            start_at += total
            r = self.search_issues(jql, startAt=start_at, expand=expand)
            total = len(r)

    def search_filters_gen(self, expand=None):
        start_at = 0
        result = []

        r = self.search_filters(startAt=start_at, expand=expand)
        total = len(r)
        while total != 0:
            for i in r:
                yield i
            start_at += total
            r = self.search_filters(startAt=start_at, expand=expand)
            total = len(r)


