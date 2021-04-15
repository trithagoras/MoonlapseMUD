import configparser
import os

_CLIENT_DIR = os.path.dirname(os.path.realpath(__file__))
_CFG_FNAME = os.path.join(_CLIENT_DIR, 'user_settings.conf')
_config = configparser.ConfigParser()
_config.read(_CFG_FNAME)

SAVED_USERNAME = 'saved_username'


def _save_configfile():
    with open(_CFG_FNAME, 'w') as cfg_file:
        _config.write(cfg_file)


def get_config_option(option: str) -> str:
    try:
        return _config['DEFAULT'][option]
    except FileNotFoundError:
        pass
    except KeyError:
        pass
    return ''


def set_config_option(option: str, value: str):
    _config['DEFAULT'][option] = value
    _save_configfile()

def remove_config_option(option: str):
    if _config.has_option('DEFAULT', option):
        _config.remove_option('DEFAULT', option)
        _save_configfile()