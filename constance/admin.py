import hashlib
from datetime import date, datetime, time
from decimal import Decimal
from operator import itemgetter

from django import forms
from django.conf import settings as django_settings
from django.contrib import admin, messages
from django.contrib.admin import widgets
from django.contrib.admin.options import csrf_protect_m
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.forms import fields
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils import six
from django.utils.formats import localize
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from leonardo.forms import Layout, SelfHandlingForm, Tab, TabHolder

from .forms import JSONTextArea, JsonField
from . import LazyConfig, settings

try:
    from django.utils.encoding import smart_bytes
except ImportError:
    from django.utils.encoding import smart_str as smart_bytes

try:
    from django.conf.urls import patterns, url
except ImportError:  # Django < 1.4
    from django.conf.urls.defaults import patterns, url


config = LazyConfig()


NUMERIC_WIDGET = forms.TextInput(attrs={'size': 10})

INTEGER_LIKE = (fields.IntegerField, {'widget': NUMERIC_WIDGET})
STRING_LIKE = (fields.CharField, {
    'widget': forms.Textarea(attrs={'rows': 3}),
    'required': False,
})


DICT_LIKE = (JsonField, {
    'widget': JSONTextArea(attrs={'rows': 10, 'cols': 30}),
    'required': False,
})

FIELDS = {
    bool: (fields.BooleanField, {'required': False}),
    int: INTEGER_LIKE,
    Decimal: (fields.DecimalField, {'widget': NUMERIC_WIDGET}),
    str: STRING_LIKE,
    list: STRING_LIKE,
    dict: DICT_LIKE,
    datetime: (fields.DateTimeField, {'widget': widgets.AdminSplitDateTime}),
    date: (fields.DateField, {'widget': widgets.AdminDateWidget}),
    time: (fields.TimeField, {'widget': widgets.AdminTimeWidget}),
    float: (fields.FloatField, {'widget': NUMERIC_WIDGET}),
}


def parse_additional_fields(fields):
    for key in fields:
        field = fields[key]

        field[0] = import_string(field[0])

        if 'widget' in field[1]:
            klass = import_string(field[1]['widget'])
            field[1]['widget'] = klass(
                **(field[1].get('widget_kwargs', {}) or {}))

            if 'widget_kwargs' in field[1]:
                del field[1]['widget_kwargs']

    return fields

FIELDS.update(parse_additional_fields(settings.ADDITIONAL_FIELDS))

if not six.PY3:
    FIELDS.update({
        long: INTEGER_LIKE,
        unicode: STRING_LIKE,
    })


class ConstanceForm(SelfHandlingForm):
    version = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, initial, *args, **kwargs):
        super(ConstanceForm, self).__init__(*args, initial=initial, **kwargs)
        version_hash = hashlib.md5()

        # inicialize tabs
        self.helper.layout = Layout(TabHolder(), 'version',)
        # format helptext as inline blocks
        self.helper.help_text_inline = True

        for group_name, group_fields in six.iteritems(settings.CONFIG_GROUPS):

            tab = Tab(group_name.replace("_", " ").capitalize())

            for name, options in group_fields.items():
                default, help_text = options[0], options[1]

                if len(options) == 3:
                    config_type = options[2]
                else:
                    config_type = type(default)

                if config_type not in FIELDS:
                    raise ImproperlyConfigured(_("Constance doesn't support "
                                                 "config values of the type "
                                                 "%(config_type)s. Please fix "
                                                 "the value of '%(name)s'.")
                                               % {'config_type': config_type,
                                                  'name': name})
                field_class, _kwargs = FIELDS[config_type]
                _kwargs['help_text'] = help_text
                self.fields[name] = field_class(label=name, **_kwargs)

                tab.append(name)

            version_hash.update(smart_bytes(initial.get(name, '')))
            self.helper.layout[0].append(tab)
        self.initial['version'] = version_hash.hexdigest()

    def handle(self, request, data):
        for name in self.cleaned_data.keys():
            if not name == "version":
                value = self.cleaned_data.get(name, settings.CONFIG.get(name)[0])
                setattr(config, name, value)
                # set to settings module
                setattr(django_settings, name, value)
        messages.success(request, _('Settings was successfully saved.'))
        return True

    def save(self):
        for key in self.cleaned_data.keys():
            if not key == "version":
                value = self.cleaned_data[key]
                setattr(config, key, value)
                # set to settings module
                setattr(django_settings, key, value)

    def clean_version(self):
        value = self.cleaned_data['version']
        if value != self.initial['version']:
            raise forms.ValidationError(_('The settings have been modified '
                                          'by someone else. Please reload the '
                                          'form and resubmit your changes.'))
        return value


class ConstanceAdmin(admin.ModelAdmin):

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.module_name
        return patterns('',
                        url(r'^$',
                            self.admin_site.admin_view(self.changelist_view),
                            name='%s_%s_changelist' % info),
                        url(r'^$',
                            self.admin_site.admin_view(self.changelist_view),
                            name='%s_%s_add' % info),
                        )

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        # First load a mapping between config name and default value
        if not self.has_change_permission(request, None):
            raise PermissionDenied

        default_initial = ((name, options[0])
                           for name, options in settings.CONFIG.items())
        # Then update the mapping with actually values from the backend
        initial = dict(default_initial,
                       **dict(config._backend.mget(settings.CONFIG.keys())))
        form = ConstanceForm(initial=initial)
        if request.method == 'POST':
            form = ConstanceForm(data=request.POST, initial=initial)
            if form.is_valid():
                form.save()
                # In django 1.5 this can be replaced with self.message_user
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _('Live settings updated successfully.'),
                )
                return HttpResponseRedirect('.')
        context = {
            'config': [],
            'title': _('Constance config'),
            'app_label': 'constance',
            'opts': Config._meta,
            'form': form,
            'media': self.media + form.media,
        }
        for name, options in settings.CONFIG.items():
            default, help_text = options[0], options[1]
            # First try to load the value from the actual backend
            value = initial.get(name)
            # Then if the returned value is None, get the default
            if value is None:
                value = getattr(config, name)
            context['config'].append({
                'name': name,
                'default': localize(default),
                'help_text': _(help_text),
                'value': localize(value),
                'modified': value != default,
                'form_field': form.fields.get(name, None),
            })
        context['config'].sort(key=itemgetter('name'))
        context_instance = RequestContext(request,
                                          current_app=self.admin_site.name)
        return render_to_response('admin/constance/change_list.html',
                                  context, context_instance=context_instance)

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, request, obj=None):
        if settings.SUPERUSER_ONLY:
            return request.user.is_superuser
        return super(ConstanceAdmin, self).has_change_permission(request, obj)


class Config(object):

    class Meta(object):
        app_label = 'constance'
        object_name = 'Config'
        model_name = module_name = 'config'
        verbose_name_plural = _('config')
        get_ordered_objects = lambda x: False
        abstract = False
        swapped = False

        def get_change_permission(self):
            return 'change_%s' % self.model_name

    _meta = Meta()


admin.site.register([Config], ConstanceAdmin)
