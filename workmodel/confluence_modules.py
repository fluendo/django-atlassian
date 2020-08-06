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
            }
        ]
    }
]
