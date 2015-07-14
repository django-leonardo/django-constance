from . import settings, utils
from django.conf import settings as django_settings


class Config(object):
    """
    The global config wrapper that handles the backend.
    """
    def __init__(self):
        super(Config, self).__setattr__('_backend',
            utils.import_module_attr(settings.BACKEND)())

    def __getattr__(self, key):
        try:
            default, help_text = settings.CONFIG[key]
        except KeyError:
            raise AttributeError(key)
        result = self._backend.get(key)
        # use Django settings as primary source of default
        # for example DEBUG if is in django settings will be set as default
        if hasattr(django_settings, key) or result is None:
            default = getattr(django_settings, key, default)
            setattr(self, key, default)
            return default
        return result

    def __setattr__(self, key, value):
        if key not in settings.CONFIG:
            raise AttributeError(key)
        self._backend.set(key, value)

    def __dir__(self):
        return settings.CONFIG.keys()
