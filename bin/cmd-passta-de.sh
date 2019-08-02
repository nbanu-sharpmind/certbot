BASE_DIR=/share/sharpmind/letsencrypt

../venv/bin/certbot certonly \
    --verbose \
    --debug \
    --config-dir $BASE_DIR/config \
    --work-dir $BASE_DIR/work \
    --logs-dir $BASE_DIR/logs  \
    --non-interactive \
    --agree-tos \
    --email is@sharpmind.de \
    --dns-checkdomain \
    --dns-checkdomain-credentials $BASE_DIR/key/checkdomain_key.ini \
    --domain passta.de
