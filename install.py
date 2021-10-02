#!/usr/bin/env python3

import json
import os

# Check if running as root
if os.geteuid() != 0:
    print('Nessus install script must run as root')
    quit()

# Set variables
nessus_installer = '/nessus_pkg/nessus.deb'
config = {'user': {'username': 'admin', 'password': 'password', 'role': 'system_administrator'}}
activation_code = ''

# Run installer
os.system('dpkg -i ' + nessus_installer)

# Create user
with open('/opt/nessus/var/nessus/config.json', 'w') as config_file:
    json.dump(config, config_file)

# Set activation code
os.system('/opt/nessus/sbin/nessuscli fetch --register ' + activation_code)

# Start Nessus
os.system('systemctl start nessusd')
