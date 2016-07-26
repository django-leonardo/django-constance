from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings
from django.conf import global_settings as django_global_settings

import json


def _load_dict(value):
    try:
        return json.loads(value)
    except:
        # TODO log me here
        pass
    return value


class ConstanceConfig(AppConfig):
    name = 'constance'
    verbose_name = _('Constance')

    def ready(self):

        # optionaly copy all live configuration to main settings
        from . import config

        for k in dir(config):
            # just only if is not present in settings

            try:
                if k not in dir(django_settings) \
                        or k in dir(django_global_settings):

                    # get value from backend
                    value = config._backend.get(k)

                    if value is not None:
                        setattr(django_settings, k, _load_dict(value))

            except:
                # TODO: log me here
                pass
