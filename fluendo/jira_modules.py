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
        ],
        "jiraIssueGlances": [
            {
                "icon": {
                    "width": 16,
                    "height": 16,
                    "url": "https://web-fluendo.s3.amazonaws.com/static/img/favicon.png"
                },
                "content": {
                    "type": "label",
                    "label": {
                        "value": "Open Fluendo"
                    }
                },
                "target": {
                  "type": "web_panel",
                  "url": "{% url 'fluendo-customers-view' %}?key={issue.key}",
                },
                "name": {
                    "value": "Fluendo"
                },
                "conditions": [{
                    "condition": "user_is_logged_in"
                }],
                "key": "fluendo-customer-issue-glance"
            }
        ],
        "jiraIssueFields": [
            {
                "key" : "fluendo-customer-name-field",
                "name" : {
                    "value" : "Fluendo Customer",
                },
                "description" : {
                    "value" : "Fluendo Customer"
                },
                "type": "read_only",
                "property": {
                    "path": "customer",
                    "key": "customers",
                    "type": "string"
                }
            }
        ],
    }
]

