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

import base64
import gssapi
import os
import requests
import urlparse


class HTTPBasicAuth(requests.auth.HTTPBasicAuth):
    pass


class HTTPKeystoneAuth(requests.auth.AuthBase):
    def __init__(self, token):
        super(HTTPKeystoneAuth, self).__init__()
        self.token = token

    def __call__(self, r):
        r.headers["X-Auth-Token"] = self.token
        return r


class HTTPGSSAPIAuthBase(requests.auth.AuthBase):
    def _authenticate(self, r, user_cred):
        svc_host = urlparse.urlparse(r.url).netloc
        svc_name = gssapi.gss_import_name("HTTP@" + svc_host,
                                          gssapi.GSS_C_NT_HOSTBASED_SERVICE)

        _, token = gssapi.gss_init_sec_context(user_cred, svc_name)

        r.headers["Authorization"] = "Negotiate " + base64.b64encode(token)
        return r


class HTTPGSSAPIAuth(HTTPGSSAPIAuthBase):
    def __init__(self, keytab, user):
        super(HTTPGSSAPIAuth, self).__init__()
        self.keytab = keytab
        self.user = user

    def __call__(self, r):
        cred_store = [("client_keytab", self.keytab)]
        my_cred = gssapi.gss_acquire_cred_from(cred_store, gssapi._NULL)

        username = gssapi.gss_import_name(self.user, gssapi.GSS_C_NT_USER_NAME)
        usercred = gssapi.gss_acquire_cred_impersonate_name(my_cred, username)

        return self._authenticate(r, usercred)


class HTTPGSSProxyAuth(HTTPGSSAPIAuthBase):
    def __init__(self, user):
        super(HTTPGSSProxyAuth, self).__init__()
        os.environ["GSS_USE_PROXY"] = "1"
        self.user = user

    def __call__(self, r):
        username = gssapi.gss_import_name(self.user, gssapi.GSS_C_NT_USER_NAME)
        usercred = gssapi.gss_acquire_cred(username)

        return self._authenticate(r, usercred)
