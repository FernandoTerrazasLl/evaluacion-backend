from split_settings.tools import include

from dotenv import load_dotenv

load_dotenv()

include(
    'components/auth_password_validators.py',
    'components/consts.py',
    'components/database.py',
    'components/installed_apps.py',
    'components/middleware.py',
    'components/templates.py',
)

