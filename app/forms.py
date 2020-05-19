from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from flask_wtf.file import FileField, FileRequired, FileAllowed
from app.models import User
from config import Config


class HomeForm(FlaskForm):
    category = SelectField('Category')
    month = SelectField('Month')
    year = SelectField('Year')
    submit = SubmitField('Select')


class UploadForm(FlaskForm):
    file=FileField(validators=[FileRequired(), FileAllowed(Config.ALLOWED_EXTENSIONS, 'unrecognized file type')])

class FileAdminForm(FlaskForm):
    files = SelectField('File Info')
    select = SubmitField('select file')
    delete = SubmitField('delete file')
    delete_all = SubmitField('delete all')

class MonthlyDetailForm(FlaskForm):
    pass

