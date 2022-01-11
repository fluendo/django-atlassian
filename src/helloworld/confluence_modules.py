modules = [
    {
        "dynamicContentMacros": [
            {
                "key": "helloworld-macro",
                "name": {"value": "Hello World Macro"},
                "url": "{% url 'helloworld-macro' %}",
                "description": {"value": "Says 'Hello World'."},
                "outputType": "block",
                "bodyType": "none",
            }
        ]
    }
]
