modules = [
    {
        "jiraDashboardItems": [
            {
                "description": {"value": "Transitions of issues over time"},
                "url": "{% url 'workmodel-business-time-transitions-dashboard-item' %}?dashboardItemId={dashboardItem.id}&dashboardId={dashboard.id}&view={dashboardItem.viewType}",
                "configurable": True,
                "thumbnailUrl": "{% static 'workmodel/transitions_dashboard_item_icon.png' %}",
                "name": {"value": "Transitions"},
                "key": "workmodel-transitions",
            }
        ],
        "jiraEntityProperties": [
            {
                "key": "jira-issue-leads-indexing",
                "name": {
                    "value": "Leads index",
                },
                "entityType": "issue",
                "keyConfigurations": [
                    {
                        "propertyKey": "leads",
                        "extractions": [
                            {"objectName": "product", "type": "text"},
                            {"objectName": "project", "type": "text"},
                            {"objectName": "email", "type": "text"},
                        ],
                    }
                ],
            },
            {
                "key": "workmodel-transition-time-property",
                "name": {
                    "value": "Transition time",
                },
                "entityType": "issue",
                "keyConfigurations": [
                    {
                        "propertyKey": "transitions",
                        "extractions": [
                            {
                                "objectName": "progress_summation",
                                "type": "number",
                            }
                        ],
                    }
                ],
            },
        ],
        "jiraIssueFields": [
            {
                "key": "workmodel-affected-products-field",
                "name": {"value": "Affected Products"},
                "description": {"value": "Products that are affected by an issue"},
                "type": "multi_select",
                "extractions": [{"path": "name", "type": "string", "name": "name"}],
            },
            {
                "key": "workmodel-progress-summation-field",
                "name": {
                    "value": "Summation In-Progress",
                },
                "description": {"value": "Summation of In-Progress transitions"},
                "type": "read_only",
                "property": {
                    "path": "progress_summation",
                    "key": "transitions",
                    "type": "number",
                },
            },
        ],
        "webSections": [
            {
                "key": "workmodel-admin",
                "location": "admin_plugins_menu",
                "name": {"value": "Workmodel"},
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
            },
        ],
        "generalPages": [
            {
                "url": "{% url 'workmodel-business-time-configuration' %}",
                "location": "admin_plugins_menu/workmodel-admin",
                "name": {"value": "Business Time"},
                "key": "workmodel-business-time-configuration",
            },
            {
                "url": "{% url 'workmodel-hierarchy-list' %}",
                "location": "admin_plugins_menu/workmodel-admin",
                "name": {"value": "Hierarchies"},
                "key": "workmodel-hierarchy-list",
            },
        ],
    }
]
