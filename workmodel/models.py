from django_atlassian.models.djira import Issue as JiraIssue

class Issue(JiraIssue):
    def is_parent(self):
        try:
            if len(self.links.contains):
                return True
        except:
            pass
        return super(Issue, self).is_parent()

    def has_parent(self):
        try:
            if len(self.links.is_contained_in):
                return True
        except:
            pass
        return super(Issue, self).has_parent()

    def get_parent(self):
        try:
            return self.links.is_contained_in[0]
        except:
            pass
        return super(Issue, self).get_parent()

    def get_children(self):
        try:
            return self.links.contains
        except:
            pass
        return super(Issue, self).get_children()

    def get_children(self):
        try:
            return self.links.contains
        except:
            pass
        return super(Issue, self).get_children()

    def get_accumulated_progress_time(self):
        changelog = self.get_changelog()
        statuses = self.get_statuses()
        initial_statuses = [x['name'] for x in statuses if x['statusCategory']['name'] == 'To Do']
        progress_statuses = [x['name'] for x in statuses if x['statusCategory']['name'] == 'In Progress']
        terminal_statuses = [x['name'] for x in statuses if x['statusCategory']['name'] == 'Done']
        amount = timedelta(0)
        from_time = None
        for ch in changelog['values']:
            for item in ch['items']:
                if item['field'] == 'status':
                    created = parse_datetime(ch['created'])
                    if from_time:
                        # TODO Remove the weekends to not count into the total amount
                        amount = amount + (created - from_time)
                    if item['toString'] in progress_statuses:
                        from_time = created
                    else:
                        from_time = None
        if from_time:
            amount = amount + (timezone.now() - from_time)

        return amount

    def transitions(self):
        """
        Return the posible transitions of the issue
        :return dict: Dict of Transitions
        """
        trans = dict(
            [
                (t['name'], t['id']) \
                for t in Issue.jira.transitions(self.key)
            ]
        )
        return trans

    def transition_to(self, transition):
        """
        Set the new transition str
        :param transition str: it is the string of the transition
        """
        trans = self.transitions()
        if transition in trans.keys():
            new_trans = trans[transition]
            return Issue.jira.transition_issue(self, new_trans)
        return None

    def __unicode__(self):
        return str(self.key)
