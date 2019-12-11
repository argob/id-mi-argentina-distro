#!/bin/bash
# run-webapp.sh

set -e
set -x

host="db"
until psql -h "$host" -U "postgres" -c '\l'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Starting syslog"
SERVICE='rsyslog'

if [ -f /var/run/rsyslogd.pid ]
then
    echo "$SERVICE pidfile already exist deleting..."
    rm /var/run/rsyslogd.pid
fi

service rsyslog start

python /code/manage.py setup
>&2 echo "Migrations completed - executing command"

python /code/manage.py runserver_plus 0.0.0.0:8000
