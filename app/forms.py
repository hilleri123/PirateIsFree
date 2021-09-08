from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, IntegerField, SubmitField, RadioField, FloatField, FieldList, FormField, DateTimeField, PasswordField, HiddenField
from wtforms.validators import Required, ValidationError, Email, EqualTo
from wtforms.widgets import TextArea

from datetime import datetime





class MyForm(FlaskForm):
    class Meta:
        csrf = True
    file_name = StringField('FileName', validators=[Required()])
    body = StringField('Text', widget=TextArea())
    submit = SubmitField('Ok')
    cancel = SubmitField('Cancel')

