#!/bin/sh
sudo mkdir /run/postgresql
sudo chown 1000:1000 /run/postgresql/
pg_ctl -D db/mydb -l logfile start
