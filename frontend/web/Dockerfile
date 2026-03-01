FROM nginx:1.27-alpine

# Copy static frontend files
COPY . /usr/share/nginx/html

# nginx config: serve index.html for all routes (SPA fallback)
RUN printf 'server {\n\
  listen 80;\n\
  root /usr/share/nginx/html;\n\
  index index.html;\n\
  location / {\n\
    try_files $uri $uri/ /index.html;\n\
  }\n\
  location ~* \.(css|js|png|jpg|svg|ico|woff2?)$ {\n\
    add_header Cache-Control "no-cache";\n\
  }\n\
}\n' > /etc/nginx/conf.d/default.conf

# Entrypoint: inject env vars into config.js at runtime
RUN printf '#!/bin/sh\n\
cat > /usr/share/nginx/html/js/config.js <<EOF\n\
window.API_BASE_URL = "${API_BASE_URL:-http://backend.model-platform.svc.cluster.local:8000}";\n\
window.MP_HOST_NAME = "${MP_HOST_NAME:-model-platform.com}";\n\
window.MP_REGISTRY_PATH = "${MP_REGISTRY_PATH:-registry}";\n\
window.MLFLOW_S3_ENDPOINT_URL = "${MLFLOW_S3_ENDPOINT_URL:-}";\n\
EOF\n\
exec nginx -g "daemon off;"\n' > /docker-entrypoint-override.sh && \
    chmod +x /docker-entrypoint-override.sh

EXPOSE 80

CMD ["/docker-entrypoint-override.sh"]
