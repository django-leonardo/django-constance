
from __future__ import absolute_import

import six
import os
from os.path import abspath, dirname, join, normpath
from leonardo import default, merge

EMAIL = {
    'HOST': 'mail.domain.com',
    'PORT': '25',
    'USER': 'username',
    'PASSWORD': 'pwd',
    'SECURITY': True,
}

RAVEN_CONFIG = {}

ALLOWED_HOSTS = ['*']

USE_TZ = True

DEBUG = True

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('admin', 'mail@leonardo.cz'),
)

DEFAULT_CHARSET = 'utf-8'

MANAGERS = ADMINS

SITE_ID = 1

SITE_NAME = 'hrcms'

TIME_ZONE = 'Europe/Prague'

LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('cs', 'CS'),
    ('en', 'EN'),
)

USE_I18N = True

# SOME DEFAULTS
MEDIA_ROOT = '/srv/leonardo/sites/demo/media/'
STATIC_ROOT = '/srv/leonardo/sites/demo/static/'

MEDIA_URL = '/media/'
STATIC_URL = '/static/'

TEMPLATE_CONTEXT_PROCESSORS = default.ctp

TEMPLATE_LOADERS = (
    'dbtemplates.loader.Loader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'horizon.loaders.TemplateLoader',
)

DBTEMPLATES_USE_REVERSION = True

DBTEMPLATES_MEDIA_PREFIX = '/static-/'

DBTEMPLATES_USE_CODEMIRROR = False

DBTEMPLATES_USE_TINYMCE = False

DBTEMPLATES_AUTO_POPULATE_CONTENT = True

DBTEMPLATES_ADD_DEFAULT_SITE = True

FILER_ENABLE_PERMISSIONS = True # noqa

MIDDLEWARE_CLASSES = default.middlewares

ROOT_URLCONF = 'leonardo.urls'

MARKITUP_FILTER = ('markitup.renderers.render_rest', {'safe_mode': True})

INSTALLED_APPS = default.apps

#ADMIN_TOOLS_MENU = 'hrcms.conf.menu.AdminDashboard'
#ADMIN_TOOLS_INDEX_DASHBOARD = 'hrcms.conf.menu.AdminDashboard'

# For easy_thumbnails to support retina displays (recent MacBooks, iOS)

FEINCMS_USE_PAGE_ADMIN = False

LEONARDO_USE_PAGE_ADMIN = True

FEINCMS_DEFAULT_PAGE_MODEL = 'web.Page'

##########################

TEMPLATE_DIRS = [
    os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'templates')
]

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    'compressor.finders.CompressorFinder',
)

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_URL = "/"

REDACTOR_OPTIONS = {'lang': 'en', 'plugins': [
    'table', 'video', 'fullscreen', 'fontcolor', 'textdirection']}
REDACTOR_UPLOAD = 'uploads/'

LOGOUT_ON_GET = True

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'WARNING',
        'handlers': ['console'],
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

# migrations support
MIGRATION_MODULES = {
    'application': 'leonardo.migrations.application',
    'filer': 'filer.migrations_django',
}

CRISPY_TEMPLATE_PACK = 'bootstrap'

SECRET_KEY = None

APPS = []

try:
    # full settings
    from leonardo_site.local.settings import *
except ImportError:
    pass

try:
    # local settings
    from local_settings import *
except ImportError:
    pass

REVERSION_MIDDLEWARE = [
    'reversion.middleware.RevisionMiddleware']


OAUTH_CTP = [
    "allauth.socialaccount.context_processors.socialaccount"
]

# first load some defaults

if 'media' in APPS:
    FILER_IMAGE_MODEL = 'leonardo.module.media.models.Image'

try:
    from leonardo.conf.horizon import *
    from leonardo.conf.static import *
except Exception, e:
    pass


APPLICATION_CHOICES = []


from leonardo.module.web.models import Page
from leonardo.module.web.widget import ApplicationWidget

from .base import leonardo

try:
    # override settings
    try:
        from leonardo_site.conf.feincms import *
    except ImportError:
        pass

    from django.utils.importlib import import_module  # noqa

    from django.utils.module_loading import module_has_submodule  # noqa

    widgets = {}

    for app, mod in six.iteritems(leonardo.get_app_modules(APPS)):

        # load all settings key
        if module_has_submodule(mod, "settings"):
            try:
                settings_mod = import_module(
                    '{0}.settings'.format(mod.__name__))
                for k in dir(settings_mod):
                    if not k.startswith("_"):
                        val = getattr(settings_mod, k, None)
                        globals()[k] = val
                        locals()[k] = val
            except Exception as e:
                pass

        if hasattr(mod, 'default'):

            APPLICATION_CHOICES = merge(APPLICATION_CHOICES, getattr(
                mod.default, 'plugins', []))

            INSTALLED_APPS = merge(
                INSTALLED_APPS, getattr(mod.default, 'apps', []))

            TEMPLATE_CONTEXT_PROCESSORS = merge(
                TEMPLATE_CONTEXT_PROCESSORS, getattr(
                    mod.default, 'ctp', []))
            MIDDLEWARE_CLASSES = merge(
                MIDDLEWARE_CLASSES, getattr(
                    mod.default, 'middlewares', []))
            AUTHENTICATION_BACKENDS = merge(
                AUTHENTICATION_BACKENDS, getattr(
                    mod.default, 'auth_backends', []))
            TEMPLATE_DIRS = merge(
                TEMPLATE_DIRS, getattr(
                    mod.default, 'dirs', []))
            # support for Django 1.8+
            DIRS = TEMPLATE_DIRS

            # collect grouped widgets
            widgets[getattr(mod.default, 'optgroup', app.capitalize())] = \
                getattr(mod.default, 'widgets', [])

    # register external apps
    Page.create_content_type(
        ApplicationWidget, APPLICATIONS=APPLICATION_CHOICES)

    # register widgets
    for optgroup, _widgets in six.iteritems(widgets):
        for widget in _widgets:
            Page.create_content_type(widget, optgroup=optgroup)

    Page.register_extensions(*PAGE_EXTENSIONS)
    Page.register_default_processors(
        frontend_editing=True)
except Exception, e:
    raise e

if not SECRET_KEY:
    try:
        LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'local')

        from horizon.utils import secret_key

        SECRET_KEY = secret_key.generate_or_read_from_file(os.path.join(LOCAL_PATH,
                                                                        '.secret_key_store'))
    except Exception:
        pass


# enable reversion for every req
if 'reversion' in INSTALLED_APPS:
    MIDDLEWARE_CLASSES = merge(REVERSION_MIDDLEWARE, MIDDLEWARE_CLASSES)

# FINALLY OVERRIDE ALL

try:
    # local settings
    from local_settings import *
except ImportError:
    pass

try:
    # full settings
    from project.local.settings import *
except ImportError:
    pass

# ensure if bootstra_admin is on top of INSTALLED_APPS
if 'bootstrap_admin' in INSTALLED_APPS:
    BOOTSTRAP_ADMIN_SIDEBAR_MENU = True
    # INSTALLED_APPS.remove('bootstrap_admin')
    #INSTALLED_APPS = ['bootstrap_admin'] + INSTALLED_APPS
