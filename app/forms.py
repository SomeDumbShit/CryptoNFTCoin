from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf.file import FileAllowed, FileField
from wtforms.validators import DataRequired, Email, Length

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=100)])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class AvatarUploadForm(FlaskForm):
    avatar = FileField('Загрузить аватар', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить')