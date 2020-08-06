modules = [
    {
        "jiraProjectPages": [
            {
                "key": "sales-accounts",
                "name": {
                    "value": "Accounts"
                },
                "url": "{% url 'sales-accounts-list-view' %}?projectKey=${project.key}",
                "iconUrl": "/static/atlassian/img/contacts.png",
                "weight": 1,
                "conditions": [
                    {
                        "condition": "user_is_logged_in"
                    },
                    {
                        "condition": "entity_property_exists",
                        "params":{
                            "entity": "project",
                            "propertyKey": "fluendo-accounts"
                        }
                    }
                ]
            },
            {
                "key": "sales-contacts",
                "name": {
                    "value": "Contacts"
                },
                "url": "{% url 'sales-contacts-list-view' %}?projectKey=${project.key}",
                "iconUrl": "/static/atlassian/img/contacts.png",
                "weight": 1,
                "conditions": [
                    {
                        "condition": "user_is_logged_in"
                    },
                    {
                        "condition": "entity_property_exists",
                        "params":{
                            "entity": "project",
                            "propertyKey": "fluendo-contacts"
                        }
                    }
                ]
            }
        ],
    }
]
