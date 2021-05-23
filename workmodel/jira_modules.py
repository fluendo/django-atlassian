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
            },
            {
                "key": "workmodel-transition-time-property",
                "name": {
                    "value": "Transition time",
                },
                "entityType": "issue",
                "keyConfigurations": [{
                    "propertyKey": "transitions",
                    "extractions": [{
                            "objectName": "progress_summation",
                            "type": "number",
                        }
                    ]
                }],
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
            },
            {
                "key" : "workmodel-progress-summation-field",
                "name" : {
                    "value" : "Summation In-Progress",
                },
                "description" : {
                    "value" : "Summation of In-Progress transitions"
                },
                "type": "read_only",
                "property": {
                    "path": "progress_summation",
                    "key": "transitions",
                    "type": "number"
                }
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
        "webSections": [
            {
                  "key": "workmodel-admin",
                  "location": "admin_plugins_menu",
                  "name": {
                      "value": "Workmodel"
                  }
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
            },
            {
                "event": "jira:issue_updated",
                "url": "{% url 'workmodel-issue-updated' %}",
            }
        ],
        "generalPages": [
            {
                "url": "{% url 'workmodel-jira-configuration' %}",
                "location": "admin_plugins_menu/workmodel-admin",
                "name": {
                    "value": "Configuration"
              },
              "key": "workmodel-jira-configuration"
            }
        ],
    }
]
