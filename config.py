import os
from urllib.parse import urljoin

BOT_TOKEN = '1182143579:AAEYwVpGe5hEOtJnqOB6M1QlNh7G7sGsHBA'
PROXY_URL = 'socks5://178.128.203.1:1080'
PROXY_LOGIN = 'student'
PROXY_PW = 'TH8FwlMMwWvbJF8FYcq0'
WEBHOOK_HOST = 'https://tranduchieubot.herokuapp.com/'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = '8443'

WEBHOOK_URL = urljoin(WEBHOOK_HOST, WEBHOOK_PATH)

WEBHOOK_SSL_CERT = 'certificate/PUBLIC.pem'
WEBHOOK_SSL_PRIV = 'certificate/url_private.key'
