from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flask import Flask

from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage



#Load app and configuration
# create config variables (to be cleaned in the future)

from flasky import db
from config import config as config_set
config=config_set['tinymrp'].__dict__

folderout=config['FOLDEROUT']
fileserver_path=config['FILESERVER_PATH']
datasheet_folder=config['DATASHEET_FOLDER']
deliverables_folder=config['DELIVERABLES_FOLDER']
variables_conf=config['VARIABLES_CONF']
webfileserver=config['WEBFILESERVER']
maincols=config['MAINCOLS']
refcols=config['REFCOLS']
deliverables=config['DELIVERABLES']
webserver=config['WEBSERVER']
process_conf=config['PROCESS_CONF']
lowercase_properties=config['LOWERCASE_PROPERTIES']
property_conf=config['PROPERTY_CONF']



from .models import Part, Bom , solidbom
from sqlalchemy import or_

import os

bp = Blueprint('home', __name__)



@bp.route('/', methods=('GET', 'POST','PUT'))
def index(page=1):

     if request.method == 'POST':
        search ="%"+ request.form['search']+"%"
        #print(search)
        error = None

        if not search:
            error = 'A text string required'

        if error is not None:
            flash(error)
        else:
             
            pagination =  Part.query.filter(or_(Part.description.like(search),Part.partnumber.like(search))).order_by(Part.partnumber.desc()).paginate(
                                                 page, per_page=12,
                                                   error_out=False)
            results=pagination.items
            for part in results:
                 part.updatefilespath(webfileserver)

            return render_template('part/tinylib/allparts.html',title="Tiny MRP", parts=results,pagination=pagination)
   
     return render_template('home/index.html',title="Tiny MRP")






