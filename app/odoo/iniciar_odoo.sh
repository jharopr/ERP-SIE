#!/bin/bash
set -eu
umask 077
printf '[options]\ndata_dir = /var/lib/odoo\naddons_path = /mnt/extra-addons\nadmin_passwd = %s\nlist_db = True\nproxy_mode = True\nlimit_time_real = 1800\nlimit_time_cpu = 1200\n' "$ODOO_MASTER_PASSWORD" > /tmp/odoo.conf
# Correo saliente (aviso al dueño). Por defecto el buzón local Mailpit; Gmail u otro SMTP desde .env.
printf 'smtp_server = %s\nsmtp_port = %s\nsmtp_ssl = %s\nemail_from = %s\n' \
  "${SMTP_HOST:-mailpit}" "${SMTP_PORT:-1025}" "${SMTP_SEGURO:-false}" "${CORREO_REMITENTE:-agente-sie@mys-demo.local}" >> /tmp/odoo.conf
if [ -n "${SMTP_USUARIO:-}" ]; then
  printf 'smtp_user = %s\nsmtp_password = %s\n' "$SMTP_USUARIO" "$SMTP_CLAVE" >> /tmp/odoo.conf
fi
if [ "${1:-}" = "odoo" ]; then shift; fi
exec /entrypoint.sh odoo "$@"
