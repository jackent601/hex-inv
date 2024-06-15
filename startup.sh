#!/bin/bash

# https://www.linkedin.com/pulse/how-install-postgresql-amazon-linux-trong-luong-van-bfsqc/
sudo dnf update
sudo dnf install postgresql15.x86_64 postgresql15-server -y

sudo postgresql-setup --initdb

sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql

# Log in using the Postgres system account:
echo "set passwd for postgres"
sudo passwd postgres
su - postgres
# Now, change the admin database password:
psql -c "ALTER USER postgres WITH PASSWORD 'your-password';"
exit

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
# Connect to the PostgreSQL server as the Postgres user:
# sudo -i -u postgres psql

# # Create a new database user:
# CREATE USER hextest WITH PASSWORD 'hextest';

# # Create a new database:
# CREATE DATABASE hextest;

# # Grant all privileges on the database to the user:
# GRANT ALL PRIVILEGES ON DATABASE hextest TO hextest;

# # To list all available PostgreSQL users and databases:
# \l
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 

# Copy postgres conf
sudo cp /var/lib/pgsql/data/postgresql.conf /var/lib/pgsql/data/postgresql.conf.bck
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '0.0.0.0'/g" /var/lib/pgsql/data/postgresql.conf

sudo cp /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf.bck
sudo sed -i '$a\host     all     all     0.0.0.0/0     md5 # open everything as ec2 has Access control anyway' /var/lib/pgsql/data/pg_hba.conf

# !
# ident -> md5

python3 -m venv .hex-play
. source ./.hex-play/bin/activate
