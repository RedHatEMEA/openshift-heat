README for openshift-heat
=========================

Jim Minter \<jminter@redhat.com\>, 28/02/2014


Introduction
------------

openshift-heat is a resource plugin for OpenStack which allows Heat to
create and delete OpenShift applications as part of a larger stack
creation/deletion.


Installation
------------

1. **Install openshift-heat on the heat-engine server.**

   `# cp -a openshift-heat /usr/local/openshift-heat`

   Ensure plugin_dirs is correctly configured in /etc/heat/heat.conf:

   `plugin_dirs=/usr/local/openshift-heat`

   Restart the heat-engine service

   `# service openstack-heat-engine restart`

2. (Optional) **Create a user and service catalogue entry for OpenShift
   in OpenStack Keystone.**

   If this step is carried out, the OpenShift server URL need not be
   manually specified in each heat template.

   Choose and record a secure new service password, and run the
   following on the Keystone server:

   `# . keystonerc_admin`
   `(keystone_admin)# SERVICE_HOST=<openshift_ip> SERVICE_PASSWORD=<password> ./install.sh`

3. (Optional, requires step 2 to be complete).  **Enable OpenShift
   authentication against OpenStack Keystone using mod_auth_keystone.**

   If this step is carried out, credentials for the OpenShift service
   need not be manually specified in each heat template.

   You will need the service password created in step 2.  See the
   README for [mod_auth_keystone](https://github.com/RedHatEMEA/c-keystoneclient) for mod_auth_keystone installation
   details.


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
