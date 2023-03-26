# This is the new widget and field defintions for WTforms written by Ray BUrns
# custom widgets
from wtforms.widgets import html_params
from markupsafe import Markup
from markupsafe import Markup
# from wtforms.fields import Field

from wtforms.fields import SubmitField


class MatButtonWidget(object):
    """
    Renders a Material Icons Button
    """
    input_type = 'submit'

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()
        if 'class' not in kwargs:
            kwargs['class'] = 'materialbtn'

        # here is actual html written out
        return Markup('<button {params} title="{title}" >{label}</button>'.format(
            params=self.html_params(name=field.name, **kwargs),
            label=field.icon,
            title=field.help)
        )


class MatButtonField(SubmitField):

    widget = MatButtonWidget() # The widget to be used

    # You need to add the new keywords (help and icon) to the constructor otherwise you will get invalid
    # keyword errors.
    # label and validators must be the first two parameters
    def __init__(self, label='', validators=None, help=None, icon=None, **kwargs):
        # call the inherited constructor but only label and validators are passed
        super(MatButtonField, self).__init__(label, validators, **kwargs)
        # set instance variables for the new parameters
        self.help = help
        self.icon = icon

class TextButtonWidget(object):
    """
    Renders a Material Icons Button
    """
    input_type = 'submit'

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        # for key in kwargs:
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()
        if 'class' not in kwargs:
            kwargs['class'] = 'textbtn'

        # here is actual html written out
        return Markup('<button {params} title="{title}" >{label}</button>'.format(
            params=self.html_params(name=field.name, **kwargs),
            label=field.text,
            title=field.help)
        )


class TextButtonField(SubmitField):

    widget = TextButtonWidget() # The widget to be used

    # You need to add the new keywords (help and icon) to the constructor otherwise you will get invalid
    # keyword errors.
    # label and validators must be the first two parameters
    def __init__(self, label='', validators=None, help=None, text=None, **kwargs):

        # call the inherited constructor but only label and validators are passed
        super(TextButtonField, self).__init__(label, validators, **kwargs)
        # set instance variables for the new parameters
        self.help = help
        self.text = text
