modules = [
    {
        "dynamicContentMacros": [
            {
                "key": "metabase-item-macro",
                "name": {"value": "Metabase question or dashboard"},
                "url": "{% url 'metabase-macro-view' %}?pageId={page.id}&pageVersion={page.version}&macroId={macro.id}",
                "description": {"value": "Embed a Metabase question or dashboard."},
                "icon": {
                    "url": "https://www.metabase.com/images/logo.svg",
                    "height": 80,
                    "width": 80,
                },
                "editor": {
                    "url": "{% url 'metabase-macro-configuration' %}",
                    "editTitle": {"value": "Insert Metabase Question/Dashboard"},
                    "insertTitle": {"value": "Insert Metabase Question/Dashboard"},
                },
            }
        ],
        "webSections": [
            {
                "key": "metabase-settings",
                "location": "system.admin",
                "name": {"value": "Metabase"},
            }
        ],
        "adminPages": [
            {
                "url": "{% url 'metabase-confluence-configuration-page' %}",
                "location": "system.admin/metabase-settings",
                "name": {"value": "Configuration"},
                "key": "metabase-configuration",
            }
        ],
    }
]
