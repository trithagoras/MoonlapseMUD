import os
import sys
import django
import json
from pathlib import Path
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "connectionstrings.json"), 'r') as f:
    cs = json.load(f)

# Required for importing the networking app (upper dir)
file = Path(__file__).resolve()
root = file.parents[1]
sys.path.append(str(root))

INSTALLED_APPS = [
    'networking'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': cs['database'],
        'USER': cs['user'],
        'PASSWORD': cs['password'],
        'HOST': cs['host'],
        'PORT': cs['port']
    }
}

settings.configure(
    INSTALLED_APPS=INSTALLED_APPS,
    DATABASES=DATABASES
)

django.setup()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
