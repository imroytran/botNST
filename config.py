import os

BOT_TOKEN = os.environ['BOT_TOKEN']

WEBHOOK_HOST = os.environ['WEBHOOK_HOST']
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = 8443

WEBHOOK_SSL_CERT = 'certificate/PUBLIC.pem'
WEBHOOK_SSL_PRIV = 'certificate/url_private.key'
