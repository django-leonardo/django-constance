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

    @property
    def local_settings(self):

        if not hasattr(self, '_local_settings'):

            try:
                import local_settings
            except ImportError:
                self._local_settings = None
            else:
                self._local_settings = local_settings

        return self._local_settings

    def is_global(self, key):
        """returns True if key is in global settings
        """
        return key in dir(django_global_settings)

    def is_in_local_settings(self, key):
        """returns True if key has different value than global settings
        """

        local_settings = self.local_settings

        if local_settings:
            return key in dir(local_settings)

        local_value = getattr(django_settings, key, None)
        global_value = getattr(django_global_settings, key, None)

        return local_value != global_value

    def ready(self):

        # optionaly copy all live configuration to main settings
        from . import config

        for k in dir(config):
            # just only if is not present in settings

            try:

                if self.is_in_local_settings(k) is True:
                    continue

                # get value from backend
                value = config._backend.get(k)

                if value is not None:
                    setattr(django_settings, k, _load_dict(value))

            except:
                # TODO: log me here
                pass
