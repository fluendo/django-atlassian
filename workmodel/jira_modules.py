modules = [
    {
        "jiraEntityProperties": [
            {
                "key": "jira-issue-customers-indexing",
                "name": {
                    "value": "Customers index",
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
        "jiraIssueFields": [
            {
                "key" : "workmodel-affected-products-field",
                "name" : {
                    "value" : "Affected Products"
                },
                "description" : {
                    "value" : "Products that are affected by an issue"
                },
                "type": "multi_select",
                "extractions": [{
                    "path": "name",
                    "type": "string",
                    "name": "name"
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
            }
        ],
        "webhooks": [
            {
                "event": "connect_addon_enabled",
                "url": "{% url 'workmodel-addon-enabled' %}",
            },
            {
                "event": "project_created",
                "url": "{% url 'workmodel-project-created' %}",
            },
            {
                "event": "project_updated",
                "url": "{% url 'workmodel-project-updated' %}",
            },
            {
                "event": "project_deleted",
                "url": "{% url 'workmodel-project-deleted' %}",
            }
        ]
    }
]
