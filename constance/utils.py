
try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module
