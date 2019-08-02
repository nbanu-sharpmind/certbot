BASE_DIR=/tmp/letsencrypt

[ -d $BASE_DIR ] && rm -rf $BASE_DIR
mkdir $BASE_DIR


../venv/bin/certbot certonly \
    --dry-run \
    --verbose \
    --debug \
    --config-dir $BASE_DIR/config \
    --work-dir $BASE_DIR/work \
    --logs-dir $BASE_DIR/logs  \
    --non-interactive \
    --agree-tos \
    --email is@sharpmind.de \
    --dns-checkdomain \
    --dns-checkdomain-credentials /share/sharpmind/letsencrypt/key/checkdomain_key.ini \
    --domain mail.passta.de
