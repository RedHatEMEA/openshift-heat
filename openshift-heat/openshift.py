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

from api import API
from heat.engine import properties, resource
from heat.openstack.common import excutils
from oslo.config import cfg
import auth

class OpenShift(resource.Resource):
    properties_schema = {
        "url": properties.Schema(properties.STRING, "url"),
        "username": properties.Schema(properties.STRING, "username"),
        "password": properties.Schema(properties.STRING, "password"),
        "verify": properties.Schema(properties.BOOLEAN, "verify"),
        "domain": properties.Schema(properties.STRING, "domain"),
        "name": properties.Schema(properties.STRING, "name"),
        "cartridges": properties.Schema(properties.LIST, "cartridges"),
        "scale": properties.Schema(properties.BOOLEAN, "scale"),
        "gear_size": properties.Schema(properties.STRING, "gear_size"),
        "initial_git_url": properties.Schema(properties.STRING,
                                             "initial_git_url"),
        "environment_variables": properties.Schema(properties.MAP,
                                                   "environment_variables"),
        "artifact_url": properties.Schema(properties.STRING, "artifact_url"),
    }

    attributes_schema = {
        "app_url": "app_url"
    }

    def _auth(self):
        ks = self.keystone().client_v2
        username = ks.tokens.authenticate(token = self.context.auth_token).user["username"]

        if cfg.CONF.plugin_openshift.auth_mechanism == "password":
            return auth.HTTPBasicAuth(self.properties["username"], self.properties["password"])
        elif cfg.CONF.plugin_openshift.auth_mechanism == "keystone":
            return auth.HTTPKeystoneAuth(self.context.auth_token)
        elif cfg.CONF.plugin_openshift.auth_mechanism == "gssapi":
            return auth.HTTPGSSAPIAuth(cfg.CONF.plugin_openshift.keytab, username)
        elif cfg.CONF.plugin_openshift.auth_mechanism == "gssproxy":
            return auth.HTTPGSSProxyAuth(username)
        else:
            raise Exception("invalid authentication mechanism configured")

    def _resolve_attribute(self, name):
        api = API(self._url(), self._auth(), self.properties["verify"])

        if name in ["app_url"]:
            return api.application_info(self.resource_id)[name]

    def _url(self):
        if self.properties["url"]:
            return self.properties["url"]
        else:
            ks = self.keystone().client_v2
            return ks.service_catalog.get_urls(service_type = "paas")[0]

    def physical_resource_name(self):
        name = self.properties.get("name")
        if name:
            return name

        return super(OpenShift, self).physical_resource_name().replace("-", "")

    def handle_create(self):
        api = API(self._url(), self._auth(), self.properties["verify"])

        d = dict([(x, self.properties[x]) for x in ["cartridges", "scale",
                                                    "gear_size",
                                                    "initial_git_url"]])
        d["name"] = self.physical_resource_name()
        if self.properties["environment_variables"]:
            d["environment_variables"] = [{"name": x, "value": self.properties["environment_variables"][x]} for x in self.properties["environment_variables"]]

        id = api.application_create(self.properties["domain"], **d)

        if self.properties["artifact_url"]:
            try:
                api.application_deploy(id, artifact_url = self.properties["artifact_url"])
            except:
                with excutils.save_and_reraise_exception():
                    api.application_delete(id)

        self.resource_id_set(id)
        return self.resource_id

    def handle_delete(self):
        if self.resource_id is None:
            return

        api = API(self._url(), self._auth(), self.properties["verify"])
                  
        api.application_delete(self.resource_id)
        return self.resource_id


def resource_mapping():
    return {"OSE::OpenShift": OpenShift}


config_group = cfg.OptGroup("plugin_openshift")
config_opts = [
    cfg.StrOpt("auth_mechanism",
               choices = ["password", "keystone", "gssapi", "gssproxy"],
               default = "password"),
    cfg.StrOpt("keytab")
]

cfg.CONF.register_group(config_group)
cfg.CONF.register_opts(config_opts, group = config_group)
