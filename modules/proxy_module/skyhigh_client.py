import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
import logging
import urllib3
from datetime import datetime
import os
import re
from module.policy_parser import PolicyParser

# 보안 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestsWarning)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class SkyhighSWGClient:
    def __init__(self, base_url, username, password, verify_ssl=False):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session_id = None
    
    def login(self):
        login_url = urljoin(self.base_url + '/', 'login')
        response = self.session.post(login_url, auth=HTTPBasicAuth(self.username, self.password), verify=self.verify_ssl)
        여기까지 쓰다가 피곤해서 못하겠음