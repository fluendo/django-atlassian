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
                "key": "jira-issue-company-indexing",
                "name": {
                    "value": "Company Index",
                },
                "entityType": "issue",
                "keyConfigurations": [{
                    "propertyKey": "companies",
                    "extractions": [{
                            "objectName": "company",
                            "type": "text"
                        },
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
                        "value": "Company"
                    }
                },
                "target": {
                  "type": "web_panel",
                  "url": "{% url 'fluendo-company-view' %}?key={issue.key}",
                },
                "name": {
                    "value": "Company"
                },
                "conditions": [{
                    "condition": "user_is_logged_in"
                }],
                "key": "fluendo-company-issue-glance"
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
                    "key": "customers",
                    "path": "customer",
                    "type": "string"
                }
            },
            {
                "key" : "fluendo-company-name-field",
                "name" : {
                    "value" : "Fluendo Company",
                },
                "description" : {
                    "value" : "Fluendo Company"
                },
                "type": "read_only",
                "property": {
                    "key": "companies",
                    "path": "company",
                    "type": "string"
                }
            },
        ],
    }
]

