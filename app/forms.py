from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, BooleanField, RadioField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from flask_wtf.file import FileField, FileRequired, FileAllowed
from app.models import User
from config import Config


class CategorySummaryForm(FlaskForm):
    state_radio_button = RadioField('current state')
    change_state = SubmitField('update state')
    prev_states = SelectField()


class FileAdminForm(FlaskForm):
    files = SelectField('File Info')
    select = SubmitField('select file')
    delete = SubmitField('delete file')
    delete_all = SubmitField('delete all')


class HomeForm(FlaskForm):
    category = SelectField('Category')
    month = SelectField('Month')
    year = SelectField('Year')
    submit = SubmitField('Select')


class MonthlyDetailForm(FlaskForm):
    pass


class StateAdminForm(FlaskForm):
    states = SelectField('States')
    new_state = StringField()
    new_state_description = StringField()
    add_new = SubmitField('add...')
    delete = SubmitField('delete selected states')

class UploadForm(FlaskForm):
    file = FileField(validators=[FileRequired(), FileAllowed(Config.ALLOWED_EXTENSIONS, 'unrecognized file type')])
