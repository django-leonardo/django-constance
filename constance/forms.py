import json
from django import forms
from django.utils import six


class JSONTextArea(forms.Textarea):

    def render(self, name, value, attrs=None):
        if value is None:
            value = ""
        if not isinstance(value, six.string_types):
            value = json.dumps(value, indent=2, default={})
        return super(JSONTextArea, self).render(name, value, attrs)


class JsonField(forms.Field):

    widget = JSONTextArea

    def to_python(self, value):
        "Normalize data to a string."

        # Return an empty list if no input was given.
        if not value:
            return {}

        try:
            cleaned = json.loads(value)
        except Exception as e:
            raise forms.ValidationError([
                e
            ])

        return cleaned
