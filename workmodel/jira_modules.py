modules = [
    {
        "jiraEntityProperties": [
            {
                "key": "jira-issue-customers-indexing",
                "name": {
                    "value": "Customers index",
                    "i18n": "customers.index"
                },
                "entityType": "issue",
                "keyConfigurations": [{
                    "propertyKey": "customers",
                    "extractions": [{
                            "objectName": "customer",
                            "type": "text"
                        },
                        {
                            "objectName": "customer_id",
                            "type": "number"
                        }
                    ]
                }],
                "conditions": [{
                    "condition": "user_is_logged_in"
                }]
            },
            {
                "key": "jira-issue-leads-indexing",
                "name": {
                    "value": "Leads index",
                    "i18n": "leads.index"
                },
                "entityType": "issue",
                "keyConfigurations": [{
                    "propertyKey": "leads",
                    "extractions": [{
                            "objectName": "product",
                            "type": "text"
                        },
                        {
                            "objectName": "project",
                            "type": "text"
                        },
                        {
                            "objectName": "email",
                            "type": "text"
                        }
                    ]
                }]
            }
        ],
        "webPanels": [
            {
                "url": "{% url 'workmodel-customers-view' %}?key={issue.key}",
                "location": "atl.jira.view.issue.right.context",
                "weight": 50,
                "name": {
                    "value": "Fluendo"
                },
                "key": "fluendo-issue-customer",
                "conditions": [{
                    "condition": "user_is_logged_in"
                }]
            },
        ]
    }
]
