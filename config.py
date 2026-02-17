import json
import os

_config_path = os.path.join(os.path.dirname(__file__), 'config.json')

with open(_config_path, 'r', encoding='utf-8') as f:
    _cfg = json.load(f)

# Gmail
GMAIL_USER         = _cfg['gmail']['user']
GMAIL_APP_PASSWORD = _cfg['gmail']['app_password']

# OpenAI / Azure OpenAI
OPENAI_PROVIDER        = _cfg['openai']['provider']          # "azure" or "openai"
OPENAI_API_KEY         = _cfg['openai']['api_key']
OPENAI_MODEL           = _cfg['openai']['model']
AZURE_ENDPOINT         = _cfg['openai']['azure']['endpoint']
AZURE_DEPLOYMENT_NAME  = _cfg['openai']['azure']['deployment_name']
AZURE_API_VERSION      = _cfg['openai']['azure']['api_version']

# Senders（只取 enabled: true）
SENDERS = [s for s in _cfg['senders'] if s.get('enabled', True)]
