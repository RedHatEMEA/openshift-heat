#!/bin/bash

yum -y install postgresql-server
su - postgres -c initdb

echo "listen_addresses = '*'" >>/var/lib/pgsql/data/postgresql.conf
cat >>/var/lib/pgsql/data/pg_hba.conf <<'EOF'
host all postgres 0.0.0.0/0 reject
host all all 0.0.0.0/0 md5
EOF

chkconfig postgresql on
service postgresql start

createuser -s -U postgres admin
createdb -O admin -U postgres ticketmonster
echo "ALTER USER admin PASSWORD 'password'" | psql -U postgres
