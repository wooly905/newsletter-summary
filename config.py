import json
import os

_config_dir = os.path.dirname(__file__)
_config_path = os.path.join(_config_dir, 'config.json')
_secrets_path = os.path.join(_config_dir, 'config.secrets.json')


def _deep_merge(base: dict, overlay: dict) -> None:
    """Merge overlay into base in-place. Nested dicts are merged recursively."""
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


with open(_config_path, 'r', encoding='utf-8') as f:
    _cfg = json.load(f)

if not os.path.isfile(_secrets_path):
    raise FileNotFoundError(
        'config.secrets.json not found. Copy config.secrets.example.json to config.secrets.json and fill in your Gmail and OpenAI API credentials.'
    )
with open(_secrets_path, 'r', encoding='utf-8') as f:
    _secrets = json.load(f)

_deep_merge(_cfg, _secrets)

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

# Senders (Only those with enabled: true)
SENDERS = [s for s in _cfg['senders'] if s.get('enabled', True)]
