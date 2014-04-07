README for openshift-heat
=========================

Jim Minter \<jminter@redhat.com\>, 05/04/2014


Introduction
------------

openshift-heat is a resource plugin for OpenStack Heat which allows it
to create and delete OpenShift applications as part of a larger stack
creation/deletion.

openshift-heat implements authentication from Heat to the OpenShift
broker(s) using any of the following (most recommended to least
recommended):

- Kerberos authentication using constrained delegation (S4U2Self,
  S4U2Proxy) via
  [gss-proxy](http://fedoraproject.org/wiki/Features/gss-proxy)

  With this option, gss-proxy is required to be installed on the Heat
  server(s); note that gss-proxy is not currently included in RHEL6.

- Kerberos authentication using constrained delegation (S4U2Self,
  S4U2Proxy)

- Keystone authentication using
  [mod_auth_keystone](https://github.com/RedHatEMEA/c-keystoneclient)

- basic authentication specified within the Heat template itself


Installation
------------

1. **Install openshift-heat on the heat-engine server.**

   `# cp -a openshift-heat /usr/local/openshift-heat`

   Ensure plugin_dirs is correctly configured in /etc/heat/heat.conf:

   `plugin_dirs=/usr/local/openshift-heat`

   Restart the heat-engine service:

   `# service openstack-heat-engine restart`

2. (Optional) **Create a user and service catalogue entry for OpenShift
   in OpenStack Keystone.**

   If this step is carried out, the OpenShift broker URL need not be
   manually specified in each heat template.

   Please note that if you intend to use Kerberos authentication to
   the OpenShift broker, you must specify the broker hostname rather
   than IP address at this point.

   Choose and record a secure new service password, and run the
   following on the Keystone server:

   `# . keystonerc_admin`
   `(keystone_admin)# SERVICE_HOST=<openshift_hostname_or_ip> SERVICE_PASSWORD=<password> ./install.sh`

   Note that the Keystone service password is only used if Keystone
   authentication to the OpenShift broker is configured (it is
   unnecessary for the other authentication types).

3. (Optional, requires step 2 to be complete).  **Enable OpenShift
   authentication using Kerberos or Keystone.**

   If this step is carried out, credentials for the OpenShift service
   need not be manually specified in each heat template.

   If you elect to use Kerberos as the authentication mechanism,
   please note that openshift-heat will attempt to find a Kerberos
   principal with a UPN matching the end-user's Keystone username, and
   will use this principal to authenticate against the OpenShift
   broker.  In this case it is therefore highly recommended that you
   use a Kerberos authentication backend to Keystone.

   Select the technology you'll be using to authenticate Heat and its
   users to OpenShift and follow one of the following sub-sections:

   (a) **Kerberos authentication using constrained delegation
   (S4U2Self, S4U2Proxy) via
   [gss-proxy](http://fedoraproject.org/wiki/Features/gss-proxy)**

   Ensure that the OpenShift broker(s) are correctly configured to
   accept authentication using Kerberos tickets.  If in doubt, consult
   the OpenShift documentation.

   Acquire a Kerberos account with UPN for Heat.  Using a MIT KDC, the
   account will need the `OK_TO_AUTH_AS_DELEGATE` attribute, and will
   need `krbAllowedToDelegateTo` to include the OpenShift broker SPN,
   e.g. `HTTP/broker.example.com@EXAMPLE.COM`.  Equivalent
   configuration is required if using Active Directory.

   Save a keytab for Heat's Kerberos account, e.g. at /etc/heat.keytab.

   ```
chown root:root /etc/heat.keytab
chmod 0400 /etc/heat.keytab
```

   Install gssproxy and configure /etc/gssproxy/gssproxy.conf as
   follows.  Replace $UID_OF_HEAT_USER with Heat's UID as found in
   /etc/passwd.

   ```
[service/heat]
  cred_store = keytab:/etc/heat.keytab
  euid = $UID_OF_HEAT_USER
  impersonate = yes
  mechs = krb5
```

   Ensure the following configuration is present in /etc/heat/heat.conf:

   ```
[plugin_openshift]
auth_mechanism=gssproxy
```

   Restart the heat-engine service:

   `# service openstack-heat-engine restart`

   Restart the gssproxy service:

   `# service gssproxy restart`

   (b) **Kerberos authentication using constrained delegation
   (S4U2Self, S4U2Proxy)**

   Ensure that the OpenShift broker(s) are correctly configured to
   accept authentication using Kerberos tickets.  If in doubt, consult
   the OpenShift documentation.

   Acquire a Kerberos account with UPN for Heat.  Using a MIT KDC, the
   account will need the `OK_TO_AUTH_AS_DELEGATE` attribute, and will
   need `krbAllowedToDelegateTo` to include the OpenShift broker SPN,
   e.g. `HTTP/broker.example.com@EXAMPLE.COM`.  Equivalent
   configuration is required if using Active Directory.

   Save a keytab for Heat's Kerberos account, e.g. at /etc/heat.keytab.

   ```
chown heat:heat /etc/heat.keytab
chmod 0400 /etc/heat.keytab
```

   Ensure the following configuration is present in /etc/heat/heat.conf:

   ```
[plugin_openshift]
auth_mechanism=gssapi
keytab=/etc/heat.keytab
```

   Restart the heat-engine service:

   `# service openstack-heat-engine restart`

   (c) **Keystone authentication using
   [mod_auth_keystone](https://github.com/RedHatEMEA/c-keystoneclient)**

   Ensure that the OpenShift broker(s) are correctly configured to
   accept authentication using Keystone tickets.  See the README for
   [mod_auth_keystone](https://github.com/RedHatEMEA/c-keystoneclient)
   for details of how to install mod_auth_keystone on the OpenShift
   broker(s).  You will need the service password created in step 2.

   Ensure the following configuration is present in /etc/heat/heat.conf:

   ```
[plugin_openshift]
auth_mechanism=keystone
```

   Restart the heat-engine service:

   `# service openstack-heat-engine restart`


Using OSE::OpenShift
--------------------

The OSE::OpenShift resource provides the following properties:

- **url**: *string, required* if installation step 2 was not carried
  out.  URL to access the OpenShift API,
  e.g. https://$OPENSHIFT_IP/broker/rest

- **username**: *string, required* if installation step 3 was not
  carried out.  Username with which to authenticate to OpenShift.

- **password**: *string, required* if installation step 3 was not
  carried out.  Password with which to authenticate to OpenShift.

- **verify**: *boolean, optional*.  Indicates whether Heat should
  verify OpenShift's API SSL certificate.  You may wish to set this to
  False in a non-production environment.

- **domain**: *string, required*.  OpenShift domain name in which to
  create/delete the application.

- **name**: *string, optional*.  New name to give the OpenShift
  application.  An auto-generated value is used if not provided.

- **cartridges**: *list(string), required*.  One or more cartridges to
  apply to the OpenShift application.

- **scale**: *boolean, optional*.  Indicates whether the new OpenShift
  application should be scaleable.

- **initial_git_url**: *string, optional*.  The location of a code
  repository to git clone into the newly created OpenShift
  application.

- **environment_variables**: *map(string -> string), optional*.
  Additional environment variables to set within the OpenShift
  application.

The OSE::OpenShift resource provides the following attribute:

- **app_url**: *string*.  The URL of the application created by
    OpenShift.


Samples
-------

- *samples/simple_demo.yaml* creates a demo python application in
  OpenShift, given that configuration step 1 has been followed.

  Edit the url, username and password values in simple_demo.yaml
  before running the following command:

  `(keystone_demo)# heat stack-create -f simple_demo.yaml test_stack -P 'domain=$DOMAIN'`

- *samples/simple_demo_integrated.yaml* creates a demo python
  application in OpenShift, given that configuration steps 1-3 have
  been followed.

  `(keystone_demo)# heat stack-create -f simple_demo_integrated.yaml test_stack -P 'domain=$DOMAIN'`

- *samples/kitchensink_demo_integrated.yaml* creates a scaled JBoss
  "kitchensink" demo application in OpenShift, given that
  configuration steps 1-3 have been followed.

  `(keystone_demo)# heat stack-create -f kitchensink_demo_integrated.yaml test_stack -P 'domain=$DOMAIN'`

- *samples/drupal.yaml* creates a two-tier application with MariaDB
  running on Fedora on OpenStack IaaS and Drupal running in OpenShift
  PaaS.  Again, configuration steps 1-3 need to have been followed.

  Note that this example uses Heat WaitConditions; in OpenStack Havana
  a user with admin privilege is required to deploy this template.

  Complete all the missing parameters in drupal_environment.yaml then
  run:

  `(keystone_demo)# heat stack-create -f drupal.yaml -e drupal_environment.yaml test_stack`

- *samples/ticketmonster.yaml* creates a two-tier application with
  PostgreSQL running on OpenStack IaaS and Ticketmonster (JBoss EAP
  application) running in OpenShift PaaS.  Again, configuration steps
  1-3 need to have been followed.

  Note that this example uses Heat WaitConditions; in OpenStack Havana
  a user with admin privilege is required to deploy this template.

  Complete all the missing parameters in
  ticketmonster_environment.yaml then run:

  `(keystone_demo)# heat stack-create -f ticketmonster.yaml -e ticketmonster_environment.yaml test_stack`
