modules = [
    {
        "jiraDashboardItems": [
            {
              "description": {
                "value": "Metabase question/dashboard"
              },
              "url": "{% url 'metabase-dashboard-item-view' %}?dashboardItemId={dashboardItem.id}&dashboardId={dashboard.id}&view={dashboardItem.viewType}",
              "configurable": True,
              "thumbnailUrl": "https://www.metabase.com/images/logo.svg",
              "name": {
                  "value": "Metabase question/dashboard"
              },
              "key": "metabase-dashboard-item"
            }
        ],
        "webSections": [
            {
                  "key": "metabase-settings",
                  "location": "admin_plugins_menu",
                  "name": {
                      "value": "Metabase"
                  }
            }
        ],
        "generalPages": [
            {
                "url": "{% url 'metabase-jira-configuration' %}",
                "location": "admin_plugins_menu/metabase-settings",
                "name": {
                    "value": "Configuration"
              },
              "key": "metabase-configuration"
            }
        ],
    },
]
