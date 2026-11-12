#!/bin/bash
set -eu
umask 077
printf '[options]\ndata_dir = /var/lib/odoo\naddons_path = /mnt/extra-addons\nadmin_passwd = %s\nlist_db = True\nproxy_mode = True\nlimit_time_real = 1800\nlimit_time_cpu = 1200\n' "$ODOO_MASTER_PASSWORD" > /tmp/odoo.conf
if [ "${1:-}" = "odoo" ]; then shift; fi
exec /entrypoint.sh odoo "$@"
