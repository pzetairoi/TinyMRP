from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField, BooleanField, SelectField,\
    SubmitField, DateField, FieldList,FormField,SelectMultipleField
from wtforms.validators import DataRequired,InputRequired, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User
from .models import Part, Job, mongoJob, mongoPart, mongoOrder, mongoSupplier



#Testing flask WTF to make forms easier
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField,SelectField,TextAreaField,\
                     RadioField, BooleanField,HiddenField
from wtforms.validators import DataRequired
from wtforms import widgets, SelectMultipleField

from datetime import datetime, date



from pymongo import MongoClient

client = MongoClient("localhost", 27017)
mongodb=client.TinyMRP
partcol=mongodb["part"]
jobcol=mongodb["job"]
ordercol=mongodb["order"]
suppliercol=mongodb["supplier"]


#bring configset
from config import config as config_set
config=config_set['tinymrp'].__dict__
allprocesses=list(config['PROCESS_CONF'].keys())
availableprocesses=[("","")]+[(x,x) for x in allprocesses]
availableprocesses.sort()




class CreateOrder(FlaskForm):
    ordernumber = StringField("order Number", validators=[DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'order numbers must have only letters, numbers, dots or '
               'underscores')])
    description = StringField("Description")
    supplier =StringField("Supplier")
    job= SelectField('Job Number')
    
    submit = SubmitField('Create order')
  

    def validate_ordernumber(self, field):
        if mongoOrder.objects(ordernumber=field.data):
                raise ValidationError('ordernumber already in use.')




class CreateJob(FlaskForm):
    jobnumber = StringField("Job Number", validators=[DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Job numbers must have only letters, numbers, dots or '
               'underscores')])
    description = StringField("Description")
    customer =StringField("Customer")
    users=SelectMultipleField('Users')


    
    
    submit = SubmitField('Create Job')

    def validate_jobnumber(self, field):
        if mongoJob.objects(jobnumber=field.data):
                raise ValidationError('Jobnumber already in use.')

class EditJob(FlaskForm):
    jobnumber = StringField("Job Number", validators=[DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Job numbers must have only letters, numbers, dots or '
               'underscores')])
    description = StringField("Description")
    users=SelectMultipleField('Users')
    customer =StringField("Customer")


    # bom= FieldList( SelectField('Partnumber', choices=availableprocesses), min_entries=5, max_entries=15)
    
    submit = SubmitField('Modify Job')

    def validate_jobnumber(self, field):
        if mongoJob.objects(jobnumber=field.data):
                raise ValidationError('Jobnumber already in use.')


class CreateSupplier(FlaskForm):


    suppliername = StringField("Supplier name", validators=[DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Job numbers must have only letters, numbers, dots or '
               'underscores')])
    description = StringField("Description")
    address =StringField("address")
    location =StringField("location")
    contact =StringField("contact")
    processes= FieldList( SelectField('Process', choices=availableprocesses), min_entries=5, max_entries=5)
    submit = SubmitField('Create Supplier')

    def validate_suppliername(self, field):
        if mongoSupplier.objects(suppliername=field.data):
                raise ValidationError('suppliername already in use.')




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



class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class Compile(FlaskForm):

    # body = TextAreaField('Add a comment', validators=[DataRequired()])
    checkbox = BooleanField('Private?')
    category=RadioField('Comment type')#,choices=[('improvement','improvement'),('mistake','mistake'),('procurement','procurement')])
    
    standard_sets=SelectField("Standard compilation sets:",choices=[('procurementpack','Procurement Pack'),
                            ('assemblypack','Assembly pack'),('purchasepack','Purchase pack')])
    # pic_path = FileField('Attach file',validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')  
    processes = MultiCheckboxField('Process filter ')
    files = MultiCheckboxField('Files filter')
    export_opt= MultiCheckboxField('Doc Packs',choices=[('visual','Visual List'),
                ('files','Selected files'),('binder','PDF binder'),('excel','Excel BOM'),
                ('fabpack','Fabrication Pack')])
                # ,('binderprocess','Binder for processes'),
                # ('visualprocess','Visual list for processes'),('excelprocess','Processes Excel BOM')])
    bom_opt= RadioField('Depth of compiliation',choices=[('toplevel','Top Level only'),('full','Full BOM')],
                        default='full')
    consumed_opt= RadioField('Consumed components',
                             choices=[('hide','Hide consumed'),('show','Show consumed')],
                             default='hide')
    classified_opt= RadioField('Classified components',
                             choices=[('hide','Hide classified'),('show','Show classified'),('only','Only Classified')],
                             default='show')
    filterprocess_opt= RadioField('Filter Process',
                             choices=[('yes','Only selected'),('no','All')],
                             default='no')
    watermark_opt= MultiCheckboxField('PDF binder options',choices=[('add_datasheet','Add datasheets'), ('quote','For quotation stamp'),
                ('classified','Classified stamp'),('approved','Approval stamp')])
    
    
    partnumber=HiddenField()
    revision=HiddenField()



