from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings

import json


def _load_dict(value):
    try:
        value = json.loads(value)
    except:
        # TODO log me here
        pass
    return value


class ConstanceConfig(AppConfig):
    name = 'constance'
    verbose_name = _('Constance')

    def ready(self):
        try:
            # optionaly copy all live configuration to main settings
            from . import config

            for k in dir(config):
                # just only if is not present in settings

                if k not in dir(django_settings):
                    setattr(django_settings, k, _load_dict(getattr(config, k)))
        except:
            # TODO: log me here
            pass
