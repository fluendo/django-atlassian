modules = [
    {
        "jiraIssueFields": [
            {
                "key": "feedback-votes",
                "description": {
                    "value": "Number of positive or negative votes given to a feature"
                },
                "type": "number",
                "name": {"value": "Feedback Votes"},
            }
        ],
        "jiraWorkflowPostFunctions": [
            {
                "key": "postfunction-increment-field",
                "description": {"value": "Increments an issue field by one"},
                "name": {"value": "Increment Issue Field"},
                "create": {"url": "{% url 'feedback-increment-create' %}"},
                "view": {
                    "url": "{% url 'feedback-increment-view' %}{postFunction.config}/"
                },
                "edit": {
                    "url": "{% url 'feedback-increment-create' %}{postFunction.config}/"
                },
                "triggered": {"url": "{% url 'feedback-increment-triggered' %}"},
            },
            {
                "key": "postfunction-decrement-field",
                "description": {"value": "Decrement an issue field by one"},
                "name": {"value": "Decrement Issue Field"},
                "create": {"url": "{% url 'feedback-decrement-create' %}"},
                "view": {
                    "url": "{% url 'feedback-decrement-view' %}{postFunction.config}/"
                },
                "edit": {
                    "url": "{% url 'feedback-decrement-create' %}{postFunction.config}/"
                },
                "triggered": {"url": "{% url 'feedback-decrement-triggered' %}"},
            },
        ],
    }
]
