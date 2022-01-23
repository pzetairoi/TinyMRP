from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, DateField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User
from .models import Part, Job


#Testing flask WTF to make forms easier
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField,SelectField,TextAreaField, RadioField
from wtforms.validators import DataRequired

from datetime import datetime, date


class CreateJob(FlaskForm):
    jobnumber = StringField("Job Number", validators=[DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Job numbers must have only letters, numbers, dots or '
               'underscores')])



    description = StringField("Description")
    customer =StringField("Customer")
    # date_due=StringField("Due Date")
    submit = SubmitField('Create Job')


    def validate_jobnumber(self, field):
        if Job.query.filter_by(jobnumber=field.data).first():
            raise ValidationError('Jobnumber already in use.')



class UploadForm(FlaskForm):
    file = FileField('Attach file',validators=[FileRequired()])
    submit = SubmitField('Submit')


class PartComment(FlaskForm):
    body = TextAreaField('Add a comment', validators=[DataRequired()])
    category=RadioField('Comment type', validators=[DataRequired()],choices=[('review','Design review'),('improvement','improvement'),('mistake','mistake'),('procurement','procurement'),('ideas','ideas')])
    pic_path = FileField('Attach file',validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')


class PartReport(FlaskForm):
    body = TextAreaField('Add a comment', validators=[DataRequired()])
    category=RadioField('Comment type',choices=[('improvement','improvement'),('mistake','mistake'),('procurement','procurement')])
    pic_path = FileField('Attach file',validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')    
