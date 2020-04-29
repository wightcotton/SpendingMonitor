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

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()]) #, Email()
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class UploadForm(FlaskForm):
    file=FileField(validators=[FileRequired(), FileAllowed(Config.ALLOWED_EXTENSIONS, 'unrecognized file type')])

class FileAdminForm(FlaskForm):
    files = SelectField('File Info')
    select = SubmitField('select file')
    delete = SubmitField('delete file')
    delete_all = SubmitField('delete all')

class MonthlyDetailForm(FlaskForm):
    pass

