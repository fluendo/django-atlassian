# -*- coding: utf-8 -*-

class Addon(object):
    def __init__(self, *args, **kwargs):
        pass

    def register(self, host, username, password, url):
        # rest/plugins/1.0/
        # reqObject.headers = {'content-type': 'application/vnd.atl.plugins.remote.install+json'}; 
        #            reqObject.body = JSON.stringify({pluginUri: descriptorUrl});
        #            reqObject.jar = false;
        #            request.post(reqObject,

    
    def unregister(self, host, username, password, url):
