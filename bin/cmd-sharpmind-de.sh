# for domain with wild-card (*) we need to add '--server https://acme-v02.api.letsencrypt.org/directory'

BASE_DIR=/share/sharpmind/letsencrypt

../venv/bin/certbot certonly \
    --verbose \
    --debug \
    --config-dir $BASE_DIR/config \
    --work-dir $BASE_DIR/work \
    --logs-dir $BASE_DIR/logs  \
    --server https://acme-v02.api.letsencrypt.org/directory \
    --non-interactive \
    --agree-tos \
    --email is@sharpmind.de \
    --dns-checkdomain \
    --dns-checkdomain-credentials $BASE_DIR/key/checkdomain_key.ini \
    --domain '*.sharpmind.de'
