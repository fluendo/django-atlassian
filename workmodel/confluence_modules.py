modules = [
    {
        "dynamicContentMacros": [
             {
                "key": "initiative-status-macro",
                "name": {
                    "value": "Initiative Status"
                },
                "url": "{% url 'workmodel-initiative-status' %}?initiativeKey={key}",
                "description": {
                    "value": "Displays the status of the children issues of an initiative."
                },
                "parameters": [
                    {
                       "identifier": "key",
                       "name": {
                         "value": "Initiative issue key"
                       },
                       "type": "string",
                       "required": True,
                       "multiple": False,
                       "hidden": False
                   }
               ],
                "outputType": "inline",
                "bodyType": "none"
             },
             {
                "key": "issue-versions-macro",
                "name": {
                    "value": "Issue versions"
                },
                "url": "{% url 'workmodel-issue-versions' %}?issueKey={key}",
                "description": {
                    "value": "Displays a table of versions associated with an issue or a descendant."
                },
                "parameters": [
                    {
                       "identifier": "key",
                       "name": {
                         "value": "Issue key"
                       },
                       "type": "string",
                       "required": True,
                       "multiple": False,
                       "hidden": False
                   }
               ],
                "outputType": "block",
                "bodyType": "none"
            }
        ]
    }
]
