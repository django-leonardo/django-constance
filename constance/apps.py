from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings


class ConstanceConfig(AppConfig):
    name = 'constance'
    verbose_name = _('Constance')

    def ready(self):
        try:
            # optionaly copy all live configuration to main settings
            from . import config

            for k in dir(config):
                setattr(django_settings, k, getattr(config, k))
        except Exception:
            # in some environment may failed
            # swallowed
            pass
