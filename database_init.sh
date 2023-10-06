#!/bin/sh
#
# Run it with the database name like
#  ./database_init.sh dbName
initdb -D db/mydb --no-locale --encoding=UTF8
pg_ctl -D db/mydb -l logfile start
createdb $1
pg_ctl -D db/mydb stop
