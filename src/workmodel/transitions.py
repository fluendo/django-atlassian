# -*- coding: utf-8 -*-

import bisect 
import datetime

def all_equal(iterator):
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == x for x in iterator)


class Transition(object):
    IN_PROGRESS = 'In Progress'
    DONE = 'Done'
    TO_DO = 'To Do'
    NONE = 'None'

    def __init__(self, from_date, to_date, status):
        self.from_date = from_date
        self.to_date = to_date
        self.status = status

    def to_days(self):
        # Get the timespan
        daygenerator = (self.from_date + datetime.timedelta(x + 1) for x in range((self.to_date - self.from_date).days))
        # Remove non working days
        days = sum(1 for day in daygenerator if day.weekday() < 5)
        return days

    def __str__(self):
        return "{} -> {} [{}]".format(self.from_date, self.to_date, self.status)

    def __repr__(self):
        return str(self)


class Transitions(object):
    def __init__(self, transitions=None):
        self.transitions = []
        if not transitions:
            transitions = []
        for t in transitions:
            self.transitions.append(t)

    def __len__(self):
        return len(self.transitions)

    def __iter__(self):
        return iter(self.transitions)

    def __getitem__(self, index):
        return self.transitions[index]

    def intersect(self):
        """
        Returns a new transition that is the intersection of the transitions
        This does not take into account the
        'from' or 'to' dates, only the status
        """
        t0 = self.transitions[0]
        statuses = [x.status for x in self.transitions]
        if all_equal(statuses):
            status = t0.status
        elif Transition.IN_PROGRESS in statuses:
            status = Transition.IN_PROGRESS
        elif Transition.TO_DO in statuses:
            status = Transition.TO_DO
        elif Transition.DONE in statuses:
            status = Transition.DONE
        else:
            status = Transition.NONE
        return Transition(t0.from_date, t0.to_date, status)

    def merge(self):
        merged_transitions = Transitions()
        last_ts = self.transitions[0]
        for ts in self.transitions[1:]:
            if ts.status != last_ts.status:
                new_transition = Transition(ts.to_date, last_ts.to_date, last_ts.status)
                merged_transitions.append(new_transition)
                last_ts = ts
        if len(merged_transitions):
            new_transition = Transition(ts.from_date, last_ts.to_date, last_ts.status)
            merged_transitions.append(new_transition)
        else:
            merged_transitions.append(last_ts)
        return merged_transitions

    def append(self, transition):
        self.transitions.append(transition)

    def normalize(self, dates):
        """
        Given a list of dates, generate fake transitions to match
        the number of transitions defined by the dates.
        """
        normalized_transitions = Transitions()
        i, j = 0, 0
        size_1, size_2 = len(self.transitions) + 1, len(dates)
        to_date = None
        next_status = self.transitions[0].status
        while i < size_1 and j < size_2:
            if i == size_1 - 1:
                t = self.transitions[i - 1].from_date
                status = Transition.NONE
            else:
                t = self.transitions[i].to_date
                status = self.transitions[i].status

            if t >= dates[j]:
              from_date = t
              next_status = status
              i += 1
              if t == dates[j]:
                 j += 1
            else:
              from_date = dates[j]
              j += 1

            if to_date:
                new_transition = Transition(from_date, to_date, last_status)
                normalized_transitions.append(new_transition)
            to_date = from_date
            last_status = next_status
        # append missing items
        while i < len(self.transitions):
            new_transition = self.transitions[i]
            normalized_transitions.append(new_transition)
            i += 1
        while j < size_2:
            from_date = dates[j]
            new_transition = Transition(from_date, to_date, last_status)
            normalized_transitions.append(new_transition)
            to_date = from_date
            j += 1
        return normalized_transitions

    def __str__(self):
        return str(self.transitions)

    def __repr__(self):
        return str(self)

class TransitionsCollection(object):
    def __init__(self, transitions=None):
        self.transitions = []
        if not transitions:
            transitions = []
        for t in transitions:
            self.transitions.append(t)

    def __len__(self):
        return len(self.transitions)

    def __iter__(self):
        return iter(self.transitions)

    def __getitem__(self, index):
        return self.transitions[index]

    def intersect(self):
        """
        Returns a new transition that is the intersection of the transitions
        found in the collection. This does not take into account the
        'from' or 'to' dates, only the status
        """
        ret = Transitions()
        for t in self.transitions:
            ret.append(t.intersect())
        return ret

    def append(self, transition):
        self.transitions.append(transition)

    def transpose(self):
        transposed = TransitionsCollection(map(Transitions, map(list, zip(*self.transitions))))
        return transposed

    def dates(self):
        """
        Get a descending ordered list of dates for all the transitions
        included
        """
        dates = []
        for ts in self.transitions:
            for t in ts:
                # FIXME yeah, python does not have a way to avoid duplicates in a sorted list
                if t.to_date not in dates:
                    bisect.insort(dates, t.to_date)
            if len(ts):
                start = ts[len(ts) - 1].from_date 
                if not start in dates:
                    bisect.insort(dates, start)
        # FIXME yeah, python does not have a way to insert reverse sorted items on a list
        dates.reverse()
        return dates

    def normalize(self):
        """
        Make every set of transitions have the same number of transitions creating fake ones
        """
        # Generate faked transitions by ordering both lists from greater to lesser
        dates = self.dates()
        normalized_transitions = TransitionsCollection()
        for ts in self.transitions:
            normalized_transition = ts.normalize(dates)
            normalized_transitions.append(normalized_transition)
        return normalized_transitions

    def __str__(self):
        return str(self.transitions)

    def __repr__(self):
        return str(self)
