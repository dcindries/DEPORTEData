#!/bin/sh
set -eu

envsubst '
${VITE_PUBLIC_DASHBOARD_URL}
${VITE_ADMIN_HOME_DASHBOARD_URL}
${VITE_ADMIN_TELEMETRY_DASHBOARD_URL}
${VITE_ADMIN_SECURITY_DASHBOARD_URL}
${VITE_ADMIN_USAGE_DASHBOARD_URL}
${VITE_CHATBOT_URL}
' < /usr/share/nginx/html/env-config.template.js > /usr/share/nginx/html/env-config.js

exec nginx -g 'daemon off;'
