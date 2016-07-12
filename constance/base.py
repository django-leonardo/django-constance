from . import settings, utils
from django.conf import settings as django_settings


class Config(object):
    """
    The global config wrapper that handles the backend.
    """
    def __init__(self):
        super(Config, self).__setattr__('_backend',
            utils.import_module_attr(settings.BACKEND)())

    def get_default(self, key):

        try:
            default = settings.CONFIG[key][0]
        except KeyError:
            raise AttributeError(key)

        return default

    def __getattr__(self, key):
        result = self._backend.get(key)
        # use Django settings as primary source of default
        # for example DEBUG if is in django settings will be set as default
        return getattr(django_settings, key, result or self.get_default(key))

    def __setattr__(self, key, value):
        if key not in settings.CONFIG:
            raise AttributeError(key)
        self._backend.set(key, value)

    def __dir__(self):
        return settings.CONFIG.keys()
