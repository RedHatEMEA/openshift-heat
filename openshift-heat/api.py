#!/usr/bin/python
#
# Copyright 2014 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import requests

class API(object):
    def __init__(self, url, auth, verify = True):
        self.s = requests.Session()
        self.url = url
        self.auth = auth
        self.verify = verify

    def _call(self, method, url, data = None):
        if type(self.auth) == tuple:
            r = self.s.request(method, self.url + url, data = data,
                               headers = { "Content-Type": "application/json" },
                               auth = self.auth, verify = self.verify)
        else:
            r = self.s.request(method, self.url + url, data = data,
                               headers = { "Content-Type": "application/json",
                                           "X-Auth-Token": self.auth },
                               verify = self.verify)

        if r.status_code / 100 != 2:
            raise Exception("Unexpected HTTP status code %u" % r.status_code)

        return json.loads(r.content)["data"]

    def application_create(self, domain, **kwargs):
        r = self._call("POST", "/domain/%s/applications" % domain,
                       json.dumps(kwargs))
    
        return r["id"]

    def application_info(self, id):
        return self._call("GET", "/application/%s" % id)

    def application_delete(self, id):
        self._call("DELETE", "/application/%s" % id)
