import datetime
from flask import jsonify
from flask_login import login_required, current_user
from ..decorators import permission_required


#To load the views
from . import tinylib
from ..main.forms import SearchSimple
from ..models import User, Permission
#from .awsbucket import upload_file, download_file, list_files






#Load app and configuration
# create config variables (to be cleaned in the future)

from flasky import db 
from config import config as config_set



config=config_set['tinymrp'].__dict__


print(config)

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
bucket=config['BUCKET']




from flask import (
    Blueprint, flash, g, redirect, session, 
    render_template, request, url_for, send_file,
    jsonify
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename





from .forms import *
from .models import Part, Bom , solidbom, create_folder_ifnotexists, Job, Jobbom


from .report import *
from .publisher import IndexPDF, bom_to_excel, get_files,get_all_files, visual_list, label_list, loadexcelcompilelist

#For raw text queries on database
from sqlalchemy.sql import text
from sqlalchemy.sql import func
from sqlalchemy import or_ , and_,not_ , desc, asc 

import os
from pathlib import Path

import shutil
from shutil import copyfile
from werkzeug.utils import secure_filename


#Testing flask WTF to make forms easier
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed


from wtforms import StringField, SubmitField,SelectField,TextAreaField, RadioField
from wtforms.validators import DataRequired

from datetime import datetime, date







#Setup for blueprint and pagination
bp = Blueprint('part', __name__)
pagination_items=15







#Used functions

import copy
def tree_dict (partin):
    #creates a dictionary with the tree of the part
        reflist=[]
        flatbom=[]

        partin.updatefilespath(webfileserver)
        
        partdict0=partin.as_dict()
        partdict=copy.copy(partdict0)
        partdict['children']=[]
        #print(partdict)

        def loopchildren(partdict,qty,reflist):
            partnumber=partdict['partnumber']
            revision=partdict['revision']
            
            
            part_loop=Part.query.filter_by(partnumber=partnumber,revision=revision).first()
            
            
            
            children_loop=part_loop.children_with_qty()
            
            
            if len(children_loop)>0:
                #print("level",part_loop.partnumber)
                partdict['children']=[]
   
            for child_loop in children_loop:
                #print(child_loop)
                child_loop.pngpath="xxxxx"
                print(child_loop.pngpath)
                child_loop.updatefilespath(webfileserver)
                print('object',child_loop.pngpath)
                test=child_loop.pngpath
                print(test)
                child_dict0=child_loop.as_dict()
                child_dict=copy.copy(child_dict0)
                child_dict['pngpath']=test
                print('dict png path',child_dict['pngpath'])
                child_dict['branch_qty']=child_loop.qty*qty
                child_dict['qty']=child_loop.qty

                
                if  len(child_loop.children)>0:
                    
                    #try:
                        loopchildren(child_dict, child_dict['branch_qty'],reflist)
                    #except:
                     #   print("Problem with", child_loop.partnumber)
                      #  print(traceback.format_exc())

                reflist.append(((child_dict['partnumber'],child_dict['revision']),child_dict['branch_qty']))
                    
                partdict['children'].append(child_dict)
                    
        loopchildren(partdict,1,reflist)
        
        #Sum up all quantities and compile flatbom
        resdict={}
        for item,q in reflist:
            total=resdict.get(item,0)+q
            resdict[item]=total
        
        for partrev in resdict.keys():
            flatbom.append({'partnumber':partrev[0],'revision':partrev[1],'total_qty':resdict[partrev]})
            #part.qty=resdict[part]
            #flatbom.append(part)
        
        #flatbom.sort(key=lambda x: (x.category,x.supplier,x.oem,x.approved,x.partnumber))
        
        #print(len(flatbom))
        #print(flatbom)
        partdict['flatbom']=flatbom
        
        return partdict


@tinylib.route('/api/test/partnumber=<partnumber>/revision=<revision>', methods=('GET', 'POST'))
def gettinyid(partnumber,revision):
    query = Part.query
    part = query.filter(db.or_(
            Part.partnumber.like(f'%{partnumber}%'),
            Part.description.like(f'%{revision}%')
        )).first()

    # response
    return jsonify(part.to_dict())




@tinylib.route('/api/part', methods=('GET', 'POST'))
@login_required
def partdata():
    query = Part.query

    #Global search filter
    search = request.args.get('search[value]')


    if search:
        query = query.filter(db.or_(
            Part.partnumber.like(f'%{search}%'),
            Part.description.like(f'%{search}%')
        ))
    
    #Cols search filter
    search = request.args.get('columns[1][search][value]')
    if search:  query = query.filter(Part.partnumber.like(f'%{search}%'))
    search = request.args.get('columns[2][search][value]')
    if search:  query = query.filter(Part.revision.like(f'%{search}%'))
    search = request.args.get('columns[3][search][value]')
    if search:  query = query.filter(Part.description.like(f'%{search}%'))
    search = request.args.get('columns[4][search][value]')
    if search:  query = query.filter(Part.process.like(f'%{search}%'))
    search = request.args.get('columns[5][search][value]')
    if search:  query = query.filter(Part.process2.like(f'%{search}%'))
    search = request.args.get('columns[6][search][value]')
    if search:  query = query.filter(Part.process3.like(f'%{search}%'))
    search = request.args.get('columns[7][search][value]')
    if search:  query = query.filter(Part.finish.like(f'%{search}%'))




    
    total_filtered = query.count()
    query = query.order_by(Part.id.desc())

    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f'order[{i}][column]')


        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        if col_name not in ['partnumber', 'description', 'process']:
            col_name = 'partnumber'

        descending = request.args.get(f'order[{i}][dir]') == 'desc'
        col = getattr(Part, col_name)
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)

    
    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    query = query.offset(start).limit(length)
    

    tabledata={'data': [part.to_dict() for part in query],
        'recordsFiltered': total_filtered,
        'recordsTotal': query.count(),
        'draw': request.args.get('draw', type=int),
    }


    # response
    return jsonify(tabledata)
    




@tinylib.route('/inventory', methods=('GET', 'POST'))
@login_required
def allparts():
    
    ##Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform= SearchSimple()
    if searchform.validate_on_submit() :
        searchstring=searchform.search.data
        session['search']=searchstring
        return redirect(url_for('tinylib.search',searchstring=searchstring,page=1, searchform=searchform ))
         
   
    
    #allparts=Part.query.filter(Part.asset!="").filter(Part.asset!="FALSE").filter(Part.asset!="False").filter(Part.process!="hardware").order_by(Part.id.desc())
    allparts=Part.query
    total=Part.query.count()
    allparts=allparts.filter(or_(Part.id>total-30,Part.id<total-30))

   
    print(config['PROCESS_LEGEND'])

    return render_template('tinylib/part/inventory.html',title="Part list", searchform=searchform, legend=config['PROCESS_LEGEND'])




# @tinylib.route('/part', methods=('GET', 'POST'))
# #@tinylib.route('/part/page/<int:page>', methods=('GET', 'POST'))
# @login_required
# def allparts(page=1):
    
#     ##Simple search snippet to add to every view   methods=['GET', 'POST'])
#     searchform= SearchSimple()
#     if searchform.validate_on_submit() :
#         searchstring=searchform.search.data
#         session['search']=searchstring
#         return redirect(url_for('tinylib.search',searchstring=searchstring,page=1, searchform=searchform ))
         
#     page = request.args.get('page', page, type=int)
#     print(page)
    
    
#     #allparts=Part.query.filter(Part.asset!="").filter(Part.asset!="FALSE").filter(Part.asset!="False").filter(Part.process!="hardware").order_by(Part.id.desc())
#     allparts=Part.query.filter(Part.process!="hardware").order_by(Part.id.desc())
#     total=Part.query.count()
#     allparts=allparts.filter(or_(Part.id>total-30,Part.id<total-30))
#     pagination = allparts.paginate(
#         page, pagination_items,
#         error_out=False)
#     parts = pagination.items



#     for part in parts:
#         part.updatefilespath(webfileserver)
#         #print (part.pdf)
   
#     print(config['PROCESS_LEGEND'])

#     return render_template('tinylib/part/allparts.html',title="Part list", parts=parts,pagination=pagination,page=1, searchform=searchform, legend=config['PROCESS_LEGEND'])




@tinylib.route('/part/search', methods=('GET', 'POST'))
@tinylib.route('/part/search/<searchstring>/<int:page>', methods=('GET', 'POST'))
@login_required
def search(searchstring="aws",page=1):
    searchform= SearchSimple()
    search="%"+ searchstring+"%"
    search="%"+ session['search']+"%"
    # print(session['search'])

    if request.method == 'POST':
        searchstring=request.form['search']
        session['search']=searchstring
        search ="%"+ searchstring+"%"
        
        return redirect(url_for('tinylib.search',searchstring=searchstring,page=1, searchform=searchform ))
        
    
    allparts=Part.query.filter(or_(Part.description.like(search),
                               Part.partnumber.like(search))).order_by(Part.id.desc())
    #allparts=allparts.filter(not_(Part.partnumber.like("opy of"))).filter(Part.revision!="")
           
    
    if request.method == 'GET' :
        
        # print("GET in search.py")
        # print(searchstring)
        # pagination = allparts.paginate(
        #     page, pagination_items,
        #     error_out=False)
        # parts = pagination.items

        #parts=Part.query.all()

        parts=Part.query.filter(or_(Part.description.like(search),
                               Part.partnumber.like(search))).order_by(Part.id.desc())
        data=[]
    
        i=0
        for part in parts:
            part.updatefilespath(webfileserver)
            part.allprocesses=part.process + " "+part.process2 + " "+part.process3
            # partdict=part.__dict__
            # partdict.pop('_sa_instance_state')
            # # print("---------------------")
            # # print("---------------------")
            # # print("---------------------")
            # print(partdict)
            # data.append(partdict)
            data.append(part)
            # i+=1
            # print(i)
            # print(part.partnumber)

        # print (data)
        # data=jsonify(data)

        print(data)
                
        return render_template('tinylib/part/searchresults.html', partsdata=data,parts=parts,searchstring=session['search'], searchform=searchform ,page=page,legend=config['PROCESS_LEGEND'])





@tinylib.route('/part/create', methods=('GET', 'POST'))
@login_required
def create():
    searchform= SearchSimple()
    if request.method == 'POST':
        partnumber = request.form['partnumber']
        revision = request.form['revision']
        description = request.form['description']
        error = None

        if not partnumber:
            error = 'Pasrtnumber is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO part (partnumber,revision, description)'
                ' VALUES (?, ?, ?)',
                (partnumber,revision, description)
            )
            db.commit()
            return redirect(url_for('tinylib.index'))

    return render_template('part/create.html')

#Keeping previous link specially for links from outside
@tinylib.route('/part/<partnumber>_rev_<revision>', methods=('GET', 'POST'))
@login_required
def details(partnumber,revision=""):
    searchform= SearchSimple()
    return redirect( url_for('tinylib.partnumber',partnumber=partnumber,revision=revision, searchform=searchform,detail="quick") )



#Detail valid inputs: "quick" and "full"
@tinylib.route('/part/detail/<detail>:<partnumber>_rev_<revision>', methods=('GET', 'POST'))
@login_required
#@tinylib.route('/part/<partnumber>_rev_<revision>/page/<int:page>', methods=('GET', 'POST'))
def partnumber(partnumber,revision="",detail="full",page=1):
    commentform=PartComment()
    searchform= SearchSimple()

    rev=""
    if revision==None or revision=="%" or revision =="":
        rev=""
    else:
        rev=revision


    if request.method == 'GET':

        #print(partnumber)
        print("-",revision)
        part=Part.query.filter_by(partnumber=partnumber,revision=rev).order_by(Part.process.desc()).first()
        if part==None:
            part=Part.query.filter_by(partnumber=partnumber).order_by(Part.revision.desc()).first()
        parts=part.children_with_qty()

        hardware=[]
        composed=[]
        composedicons=[]
        composedprocesses=[]

        #UPdate related part files location to the webserver
        part.updatefilespath(webfileserver)



        legend=config['PROCESS_LEGEND']
        needed_processes=[]
        icons=[]
        colors=[]

        #Include top part processes in the required processes
        for process in process_conf.keys():
            #To only show the used processes uncomment line below        
            if part.hasProcess(process) and  process not in needed_processes :
                        needed_processes.append(process)
        
        #Detailed part bom info check
        if detail=="full":
            #Toget the full flat bom
            flatbom=part.get_components()

            print("original flatbom length", len(flatbom))
            #To limit the amount of parts displayed - no need anymore with the full details new page
            #if len(flatbom)>350 :
            #    flatbom=[x for x in flatbom if len(x.children)>0 ]
            #    #flatbom=[x for x in flatbom if x.hasProcess("assembly") or x.hasProcess("welding") or x.hasProcess("paint") ]
            print("after reduction for too many parts", len(flatbom))


      
            for parto in flatbom:
                parto.updatefilespath(webfileserver,png_thumbnail=True)
                parto.MainProcess()
                for process in process_conf.keys():
                        if parto.hasProcess(process) and  process not in needed_processes :
                            needed_processes.append(process)
                if (not parto.process in process_conf.keys() or \
                   (parto.process2!="" and not parto.process2 in process_conf.keys() )or \
                   (parto.process3!="" and not parto.process3 in process_conf.keys() )) and \
                   "others" not in needed_processes:
                        needed_processes.append( "others")
                if  (bool(parto.process) ^ bool(parto.process2)  ^ bool(parto.process3)):
                    #print (parto.partnumber)
                    pass
                else:
                    print (parto.partnumber, parto.process,parto.process2,parto.process3)
                    composed_process=[parto.process,parto.process2,parto.process3]
                    composed_process.sort()
                    composed_process=set([x for x in composed_process if x!=""])
                    composed.append(parto)
                    parto.composed_process=composed_process
                    if len(composed_process)>1 and not composed_process in composedprocesses:
                        composedprocesses.append(composed_process)
                        comp_icon=[process_conf[process]['icon'] for process in composed_process]
                        composedicons.append(comp_icon)
                

            #PRint the composed process for checking
            for comp in composedprocesses:
                    print(comp)

             #PRint the composed process for checking
            for icon in composedicons:
                    print("icon ",icon)
        else:
            flatbom=""
        
        #To get the top level flatbom and having better resolution from them
        # due to the updatefilespath function affection all the parts (database object)
        for parto in parts:
            if parto.process=="hardware":
                hardware.append(parto)
            else:

                parto.updatefilespath(webfileserver)

                for process in process_conf.keys():
                    if parto.hasProcess(process) and  process not in needed_processes :
                        needed_processes.append(process)
        print(needed_processes)



        for parto in hardware:
            parts.remove(parto)

        parents=part.parents_with_qty()

        for parto in parents:
            parto.updatefilespath(webfileserver)

        # comments=[]
        # # for comment in part.comments:
        # #     comment.username=User.query.filter_by(id=comment.user_id).first().username
        # #     comments.append(comment)

        



        for process in needed_processes:
            try:
                icons.append(process_conf[process]['icon'])
                colors.append(process_conf[process]['color'])
            except:
                print("No icon for ", process)

        legend=[ {'process':process,'icon':'images/'+icon,'color':color} for  (process,icon,color) in zip(needed_processes,icons,colors) ]

        print("THIS IS THE ", legend)


        return render_template("tinylib/part/details.html",part=part,parts=parts,
                               hardware=hardware,parents=parents,
                               commentform=commentform,
                               #pagination="",
                            #    comments=comments,
                               flatbom=flatbom,
                               legend=legend, title=part.partnumber, processes=needed_processes, 
                               composed=composed,composedprocesses=composedprocesses, searchform=searchform)
    else:
        error = 'Cannot get part detials ' + partnumber + " rev " + revision
        flash(error)

    if request.method == 'POST':
        if 'search' in request.form:
            if  request.form[ 'search']!="":
            
                search ="%"+ request.form['search']+"%"
                session['search']=search
        
                error = None

                if not search:
                    error = 'A text string required'

                if error is not None:
                    flash(error)
                else:

                    return redirect(url_for('tinylib.search',searchstring=search,page=1 , searchform=searchform))
        else:
            part=Part.query.filter_by(partnumber=partnumber,revision=rev).first()


            if   (commentform.pic_path.data):
                f = commentform.pic_path.data
                filename = part.partnumber+"-REV-"+part.revision+ "-comment-" + datetime.now().strftime('%d_%m_%Y-%H_%M_%S')+ "-"  +  secure_filename(f.filename)
                localfilename =os.path.join(config['PIC_LOCATION'], filename)
                f.save(localfilename)
                flash('Pic uploaded successfully.')

                comment=Comment(part_id=part.id,
                            user_id=g.user['id'],
                            created=func.now(),
                            body=commentform.body.data,
                            category=commentform.category.data, 
                            pic_path=webfileserver+"/Deliverables/pic/"+filename                            
                            )
            else:
                filename =""
                comment=Comment(part_id=part.id,
                            user_id=g.user['id'],
                            created=func.now(),
                            body=commentform.body.data,
                            category=commentform.category.data, 
                            pic_path=""                            
                            )
            


            refpart=part.partnumber
            refrev=part.revision
            if refrev=="": refrev="%"
            db.session.add(comment)
            db.session.commit() 
            db.session.close()
            
            return redirect(url_for('tinylib.details',partnumber=refpart,revision=refrev, searchform=searchform,pagination="" ))
            

    
@tinylib.route('/part/uploader', methods = ['GET', 'POST'])
@login_required
def upload_file():
    bomform = UploadForm()    
    searchform= SearchSimple()
    if searchform.validate_on_submit() :
        searchstring=searchform.search.data
        session['search']=searchstring
        return redirect(url_for('tinylib.search',searchstring=searchstring,page=1, searchform=searchform ))
   

    
    

    if bomform.validate_on_submit():
        f = secure_filename(bomform.file.data.filename)
        
        folder= os.path.dirname(os.path.abspath(__file__))        
        targetfile= folder+ "/" + config['UPLOAD_PATH']+ "/" + secure_filename(f)
        print(targetfile)
        print(folderout)

        
        




        bomform.file.data.save(targetfile)

        
        
        #return "targetfile---" + targetfile + "*****  deliverables_folder----" + deliverables_folder+ "*******  fileserver_path---" + fileserver_path+ "*******  folderout---" + folderout

        bom_in=solidbom(targetfile,deliverables_folder,fileserver_path+folderout)

        


        if bom_in.revision=="":
            bom_in.revision="%25"


        flash("BOM uploaded successfully")
        # return render_template('tinylib/upload.html',upload=True, searchform=searchform , bomform=bomform)

        try:
            os.remove(targetfile)
        except:
            flash("Couldn't erase upload file ", targetfile)

        if bom_in.revision=="":
            bom_in.revision="%25"
        
        return redirect(url_for('tinylib.details',partnumber=bom_in.partnumber,revision=bom_in.revision, searchform=searchform ))            
           
    else:
        return render_template('tinylib/upload.html',upload=False, searchform=searchform , bomform=bomform)



@tinylib.route('/part/excelcompile', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def excelcompile():
    weblink=False
    excelform = UploadForm()
    searchform= SearchSimple()
    
    if searchform.validate_on_submit() :
        page=1
        search ="%"+ searchform.search.data+"%"
        searchstring=searchform.search.data
        print(search)
        error = None

        if not search:
            error = 'A text string required'

        if error is not None:
            flash(error)
        else:
            print(search,search)

            allparts=Part.query.filter(or_(Part.description.like(search),
                                        Part.partnumber.like(search))).order_by(Part.partnumber.desc())
        

            if 'rev' in request.form:
                allparts=allparts.filter(Part.revision!="")
            if 'assy' in request.form:
                allparts=allparts.filter(or_(Part.process=="assembly"))
            pagination =  allparts.paginate( page, per_page=pagination_items,
                                            error_out=False)
            parts=pagination.items
            for part in parts:
                part.updatefilespath(webfileserver, png_thumbnail=True)
            session['search']=searchstring
            print(search,search,search)
            return redirect(url_for('tinylib.search',searchstring=searchstring,page=1 ,searchform=searchform))


    
    
    if excelform.validate_on_submit():
        f = secure_filename(excelform.file.data.filename)
        
               
        print("in post")
        # f = request.files['file']
        folder= os.path.dirname(os.path.abspath(__file__))
        
        targetfile= folder+ "/" + config['UPLOAD_PATH']+ "/" + secure_filename(f)
        print(targetfile)
        
        
        try:
            os.remove(targetfile)
        except:
            pass
        excelform.file.data.save(targetfile)
        
        print(folderout)
        flatbom,listofobjects=loadexcelcompilelist(targetfile,export_objects=True)
        print(flatbom)

        


        flash("Excel file uploaded successfully")
        
        #Create export folder and alter the output folder and create it
        summaryfolder=os.getcwd()+"/temp/"+"excelcompile"+datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+"/"
        create_folder_ifnotexists(summaryfolder)
        
        bomartificial=solidbom.solidbom_from_flatbom(listofobjects,listofobjects[0],outputfolder=summaryfolder,sort=False)
        pdf_pack=IndexPDF(bomartificial,outputfolder=summaryfolder,sort=False,norefpart=True)
        
        #Copy original excel file to export folder
        shutil.copy2(Path(targetfile),Path(summaryfolder+"inputfile"+datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+".xlsx") )


        #Get all files of the flatbom
        get_all_files(flatbom,summaryfolder)

        
        

        #Compile all in a zip file
        zipfile= Path(shutil.make_archive(Path(summaryfolder), 'zip', Path(summaryfolder)))
        print("original " ,zipfile)

        path, filename = os.path.split(zipfile)
        finalfile=fileserver_path+deliverables_folder+"temp/"+filename
        print("final " ,finalfile)


        shutil.copy2(Path(zipfile),Path(finalfile) )
        
        #Remove all the temp files
        os.remove(zipfile)
        shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

        #Create the web link 
        weblink="http://"+finalfile.replace(fileserver_path,webfileserver)


        #Clean original file
        try:
            
            os.remove(targetfile)
        except:
            print("Couldn't erase upload file ", targetfile)
            flash("Couldn't erase upload file ", targetfile)


        
        return render_template('tinylib/excelcompile.html',excelform=excelform,upload=True,weblink=weblink,searchform=searchform)
            
    else:
        return render_template('tinylib/excelcompile.html',excelform=excelform,upload=False,weblink=False,searchform=searchform)

    
@tinylib.route('/part/<partnumber>_rev_<revision>/drawingpack/<components_only>', methods=('GET', 'POST'))
@login_required
def drawingpack(partnumber,revision,components_only="NO"):
    
    components_only=request.args.get('components_only',default = '*', type = str)
    print(components_only)
    print(components_only)
    print(components_only)
    print(components_only)
    print(components_only)

    if components_only=="YES":
        components_only=True
    elif components_only=="NO":
        components_only=False
    else:
        components_only=False



    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    #Set qty to one to compute the rest
    part.qty=1

    flatbom=[]
    flatbom.append(part)
    flatbom=flatbom+part.get_components(components_only=components_only)

    

    bom_solidbomobject=solidbom.solidbom_from_flatbom(flatbom,part)
    print(bom_solidbomobject.tag)


    summaryfolder=os.getcwd()+"/temp/"+bom_solidbomobject.tag+"/"
    bomtitle="-manufacturing list-"
    create_folder_ifnotexists(summaryfolder)



    print(bom_solidbomobject.folderout)
    pdf_pack=IndexPDF(bom_solidbomobject,outputfolder=summaryfolder,sort=False)
    print(pdf_pack)

    path, filename = os.path.split(pdf_pack)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename


    shutil.move(pdf_pack,finalfile )

    finalfile=finalfile.replace(fileserver_path,webfileserver)
    print(finalfile)
    print("changes?")
    

    return redirect("http://"+finalfile)

@tinylib.route('/part/<partnumber>_rev_<revision>/fabrication', methods=('GET', 'POST'))
@login_required
def fabrication(partnumber,revision):
    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
    flatbom=flatbom+part_in.get_components()

    #Extract the welding components
    if part_in.hasProcess("welding"):
        manbom=[]
        manbom.append(part_in)
    else:
        manbom= [x for x in flatbom if x.hasProcess("welding") ]

    if len(manbom)==0 and part_in.hasProcess("welding"):
        manbom.append(part_in)
    elif len(manbom)==0:
        return "NO FABRICATION AVAILABLE IN THE PARTNUMBER"
    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-fabrication_pack/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(manbom,part_in)
    bom_in.folderout=summaryfolder

    #Create list with title
    bomtitle=bom_in.tag+"- scope of supply"
    excel_list=bom_to_excel(bom_in.flatbom,bom_in.folderout,title=bomtitle,qty="qty", firstrow=1)

    #Copy root part image and drawing
    path, filename = os.path.split(part_in.pngpath)
    copyfile(part_in.pngpath,summaryfolder+filename)

    #Machined parts used in fabrication
    machined=[]



    #Loop over the fabrication components and create files
    for index,component in enumerate(manbom):
        
        #Get flatbom for each component
        com_flatbom=[]
        com_flatbom.append(component)
        com_flatbom=com_flatbom+component.get_components(components_only=False)

        #Get the machined components:
        #for mach_comp in com_flatbom:
        #    if mach_comp.hasProcess("machine"):
        #        machined.append(mach_comp)

                
        #Create the flatbom for each man item and alter the output folder and create it
        com_bom=solidbom.solidbom_from_flatbom(com_flatbom,component)
        com_bom.folderout=summaryfolder+com_bom.partnumber+"/"
        create_folder_ifnotexists(com_bom.folderout)

        #Create the drawing pack (pdf)
        com_dwgpack=IndexPDF(com_bom,outputfolder=com_bom.folderout,sort=False)

        #Get manufacturing files
        get_files(com_bom.flatbom,'dxf',com_bom.folderout)
        get_files(com_bom.flatbom,'step',com_bom.folderout)
        get_files(com_bom.flatbom,'pdf',com_bom.folderout)
        get_files(com_bom.flatbom,'png',com_bom.folderout)

        #Create the bom title
        bomtitle=com_bom.tag+"-components list"

        #Crete excelist
        excel_list=bom_to_excel(com_bom.flatbom,com_bom.folderout,title=bomtitle,qty="qty")

        print(com_bom.folderout)
        com_dwgpack=IndexPDF(com_bom,outputfolder=com_bom.folderout,sort=False)
        print(com_dwgpack)



        


    zipfile= Path(shutil.make_archive(Path(summaryfolder), 'zip', Path(summaryfolder)))
    print("original " ,zipfile)

    path, filename = os.path.split(zipfile)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename
    print("final " ,finalfile)


    shutil.copy2(Path(zipfile),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(zipfile)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)
    
    return redirect(weblink)


@tinylib.route('/part/<partnumber>_rev_<revision>/<processin>_componentsonly_<components_only>', methods=('GET', 'POST'))
@login_required
def process_docpack(partnumber,revision,processin,components_only):

    #Remove spaces from link
    process=processin.replace('%20',' ')

    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)
    

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
      
    #Check if needed to consume the welded components or not 
    if components_only=="YES":
        flatbom=flatbom+part_in.get_components(components_only=True)
        
    else:
        flatbom=flatbom+part_in.get_components(components_only=False)
        

    #Extract the process related components components
    part_in.MainProcess()
    #if part_in.hasProcess(process):
    if part_in.isMainProcess(process):
        manbom=[]
        manbom.append(part_in)
    elif components_only=="YES":
        manbom= [x for x in flatbom if x.MainProcess()==process ]
    else:
        manbom= [x for x in flatbom if x.isMainProcess(process) ]


    if len(manbom)==0 and part_in.isMainProcess(process):
        manbom.append(part_in)
    elif len(manbom)==0:
        return ("NO COMPONENTS WITH THE PROCESS " + process.upper())
    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-"+process.upper()+"-components_only_"+components_only +"_pack/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(manbom,part_in)
    bom_in.folderout=summaryfolder

    #Create list with title
    bomtitle=bom_in.tag+"- scope of supply"
    #excel_list=bom_to_excel(bom_in.flatbom,bom_in.folderout,title=bomtitle,qty="qty", firstrow=1)
    excel_list=bom_in.solidbom_to_excel(process=processin)

    #Copy root part image and drawing
    path, filename = os.path.split(part_in.pngpath)
    copyfile(part_in.pngpath,summaryfolder+filename)


    #Get manufacturing files
    if process=="machine"  or  process=="folding"  or process=="profile cut"  or process=="3d laser"   or process=="3d print"  or process=="rolling" :
        get_files(bom_in.flatbom,'step',summaryfolder)
    
    if process!="hardware":
        get_files(bom_in.flatbom,'png',summaryfolder)

    if process=="lasercut" or  process=="folding"  or  process=="machine" or process=="profile cut"   :
        get_files(bom_in.flatbom,'dxf',summaryfolder)

    get_files(bom_in.flatbom,'pdf',summaryfolder)

    #Compile all in a zip file
    zipfile= Path(shutil.make_archive(Path(summaryfolder), 'zip', Path(summaryfolder)))
    print("original " ,zipfile)

    path, filename = os.path.split(zipfile)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename
    print("final " ,finalfile)


    shutil.copy2(Path(zipfile),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(zipfile)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)
    
    return redirect(weblink)



@tinylib.route('/part/<partnumber>_rev_<revision>/<processin>_<components_only>', methods=('GET', 'POST'))
@login_required
def process_visuallist(partnumber,revision,processin,components_only):

    #Remove spaces from link
    process=processin.replace('%20',' ')


    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
       
    #Check if needed to consume the welded components or not 
    if components_only=="YES":
        flatbom=flatbom+part_in.get_components(components_only=True)
        
    else:
        flatbom=flatbom+part_in.get_components(components_only=False)
    
    



    #Extract the process related components components
    part_in.MainProcess()
    if part_in.hasProcess(process):
        manbom=[]
        manbom.append(part_in)
    elif process=="toplevel":
        manbom= [x for x in part_in.children if not x.hasProcess("hardware") ]
    elif process=="all":
        manbom= [x for x in flatbom if not x.hasProcess("hardware") ]
        #Sort the list by process
        manbom=sorted(manbom, key=lambda x: x.partnumber, reverse=False)
        manbom=sorted(manbom, key=lambda x: x.process, reverse=False)
    elif components_only=="YES":
        manbom= [x for x in flatbom if x.MainProcess()==process ]
    else:
        manbom= [x for x in flatbom if x.isMainProcess(process) ]



    if len(manbom)==0 and part_in.isMainProcess(process):
        manbom.append(part_in)
    elif len(manbom)==0:
        return ("NO COMPONENTS WITH THE PROCESS " + process.upper())
    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-"+process.upper() +"_pack/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(manbom,part_in)
    bom_in.folderout=summaryfolder

    #Assign title
    if process=="toplevel":
        visualtitle="Top level components"
    else:
        visualtitle="Visual_summary_components_only-"+components_only +"-"+process

    #Create the visual list
    visuallist=visual_list(bom_in, outputfolder=summaryfolder,title=visualtitle.replace(" ","_" ))

    #MOVE FILE to temp folder
    path, filename = os.path.split(visuallist)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename
    


    shutil.copy2(Path(visuallist),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(visuallist)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)

    print(weblink)
    
    return redirect(weblink)



@tinylib.route('/part/<partnumber>_rev_<revision>/flatbom/<components_only>', methods=('GET', 'POST'))
@login_required
def flatbom(partnumber,revision,components_only):
    

    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
    
    
    #Check if needed to consume the welded components or not 
    if components_only=="YES":
        flatbom=flatbom+part_in.get_components(components_only=True)
        
    else:
        flatbom=flatbom+part_in.get_components(components_only=False)
        

    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-bom/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(flatbom,part_in)
    bom_in.folderout=summaryfolder

    #Create the bom
    excelbom=bom_in.solidbom_to_excel()


    path, filename = os.path.split(excelbom)
    if components_only=="YES":
        finalfile=fileserver_path+deliverables_folder+"temp/COMPONENTS_ONLY-"+filename
        #print("final " ,finalfile)
    else:
        finalfile=fileserver_path+deliverables_folder+"temp/FULL_FLAT_BOM-"+filename
        #print("final " ,finalfile)


    shutil.copy2(Path(excelbom),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(excelbom)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)
    
    return redirect(weblink)



@tinylib.route('/part/<partnumber>_rev_<revision>/treeview', methods=('GET', 'POST'))
def treeview(partnumber,revision):
    searchform= SearchSimple()

    rev=""
    if revision==None or revision=="%" or revision =="":
        rev=""
    else:
        rev=revision


    if request.method == 'GET':

        part=Part.query.filter_by(partnumber=partnumber,revision=rev).order_by(Part.process.desc()).first()

        treedict=tree_dict(part)
        return render_template("tinylib/part/treeview.html",treedict=treedict, searchform=searchform)





@tinylib.route('/part/label/<partnumber>_rev_<revision>/<processin>_<components_only>', methods=('GET', 'POST'))
@login_required
def process_label_list(partnumber,revision,processin,components_only):

    #Remove spaces from link
    process=processin.replace('%20',' ')


    if revision==None or "%" in revision  or revision =="":
        rev=""
    else:
        rev=revision


    #Get the top part level object
    part_in=Part.query.filter_by(partnumber=partnumber,revision=rev).first()
    print(part_in)
    #Set qty to one to compute the rest and updatepaths
    part_in.qty=1
    part_in.updatefilespath(fileserver_path,local=True)

    #Add the top part to the list
    flatbom=[]
    flatbom.append(part_in)
       
    #Check if needed to consume the welded components or not 
    if components_only=="YES":
        flatbom=flatbom+part_in.get_components(components_only=True)
        
    else:
        flatbom=flatbom+part_in.get_components(components_only=False)
    
    



    #Extract the process related components components
    if part_in.hasProcess(process):
        manbom=[]
        manbom.append(part_in)
    elif process=="toplevel":
        manbom= [x for x in part_in.children if not x.hasProcess("hardware") ]
    elif process=="all":
        manbom= [x for x in flatbom if not x.hasProcess("hardware") ]
        #Sort the list by process
        manbom=sorted(manbom, key=lambda x: x.partnumber, reverse=False)
        manbom=sorted(manbom, key=lambda x: x.process, reverse=False)
    else:
        manbom= [x for x in flatbom if x.hasProcess(process) ]



    if len(manbom)==0 and part_in.hasProcess(process):
        manbom.append(part_in)
    elif len(manbom)==0:
        return ("NO COMPONENTS WITH THE PROCESS " + process.upper())
    
    #Create export folder and alter the output folder and create it
    summaryfolder=os.getcwd()+"/temp/"+part_in.tag+"-"+process.upper() +"_pack/"
    create_folder_ifnotexists(summaryfolder)
    
    #Create the SolidBom class object for easier referencing, and override the output folder
    bom_in=solidbom.solidbom_from_flatbom(manbom,part_in)
    bom_in.folderout=summaryfolder

    #Assign title
    if process=="toplevel":
        visualtitle="Top level components"
    else:
        visualtitle="Visual_summary_components_only-"+components_only +"-"+process

    #Create the visual list
    visuallist=label_list(bom_in, outputfolder=summaryfolder,title=visualtitle.replace(" ","_" ))

    #MOVE FILE to temp folder
    path, filename = os.path.split(visuallist)
    finalfile=fileserver_path+deliverables_folder+"temp/"+filename
    


    shutil.copy2(Path(visuallist),Path(finalfile) )
    
    #Remove all the temp files
    os.remove(visuallist)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    #Create the web link 
    weblink="http://"+finalfile.replace(fileserver_path,webfileserver)

    print(weblink)
    
    return redirect(weblink)






    

#Detail valid inputs: "quick" and "full"
@tinylib.route('/part/pdf/<partnumber>_rev_<revision>', methods=('GET', 'POST'))
@login_required

def pdfwithdescription(partnumber,revision=""):
    commentform=PartComment()

    rev=""
    if revision==None or revision=="%" or revision =="":
        rev=""
    else:
        rev=revision


    if request.method == 'GET':

        #print(partnumber)
        print("-",revision)
        part=Part.query.filter_by(partnumber=partnumber,revision=rev).order_by(Part.process.desc()).first()
        if part==None:
            part=Part.query.filter_by(partnumber=partnumber).order_by(Part.revision.desc()).first()


        part.updatefilespath(webfileserver)
        #MOVE FILE to temp folder
        # flash(part.pdfpath)
        path, filename = os.path.split(part.pdfpath)
        # flash(filename)
        #remove extension
        filename=os.path.splitext(filename)[0]
        # flash(filename)

        finalfile=fileserver_path+deliverables_folder+"temp/"+filename+"_"+part.description+".pdf"
        finalfile=finalfile.replace(" ","_")
        # flash(finalfile)
        
        shutil.copy2(Path(part.pdfpath.replace(webfileserver,fileserver_path)),Path(finalfile) )
        
        #Create the web link 
        weblink="http://"+finalfile.replace(fileserver_path,webfileserver)

        #print(weblink)
        # flash(weblink)
    
        return redirect(weblink)            
        
    if request.method == 'POST':
        if 'search' in request.form:
            if  request.form[ 'search']!="":
            
                search ="%"+ request.form['search']+"%"
                session['search']=search
        
                error = None

                if not search:
                    error = 'A text string required'

                if error is not None:
                    flash(error)
                else:

                    return redirect(url_for('tinylib.search',searchstring=search,page=1 ))

            


@tinylib.route('/hello')
def hello():
    return 'Hello, World!'





@tinylib.route('/createjob', methods=['GET', 'POST'])
def createjob():
    jobs=Job.query.order_by(desc(Job.id)).limit(5)
 
    jobform = CreateJob()
    jobcreated=False
    
    ##Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform= SearchSimple()

    if searchform.validate_on_submit() :
        searchstring=searchform.search.data
        session['search']=searchstring
        return redirect(url_for('tinylib.search',searchstring=searchstring,page=1, searchform=searchform ))

    if current_user.can(Permission.WRITE) and jobform.validate_on_submit():
        print("dassdfasdfasdfas")
        job= Job(   jobnumber = jobform.jobnumber.data,
                    description = jobform.description.data,
                    customer =jobform.customer.data,
                    
                    user_id =current_user._get_current_object().id,
                    # date_due=   jobform.date_due.data,
                    )
                                  
        db.session.add(job)
        db.session.commit()
        # db.session.close()
        jobcreated=True
        flash("job created successfully")
        return redirect(url_for('tinylib.createjob', jobs=jobs,form=jobform,searchform=searchform, jobcreated=jobcreated))


    return render_template('tinylib/job_create.html', jobs=jobs,form=jobform,searchform=searchform, jobcreated=jobcreated)



def isjobnumber(jobnumber):
    job=Job.query.filter_by(jobnumber=jobnumber).first()
    if job==None:
        return False
    else: 
        
        return True

@tinylib.route('/checkjobnumber', methods=['GET','POST'])
@login_required
@permission_required(Permission.MODERATE)
def checkjobnumber():
    # resp=jsonify("Hello World")
    # resp.status_code = 200
    # resp.text="dasfasdf"
    # resp.value="dfasdfa"
    # return resp
    
    # print(jsonify(request.args))
    # print(jsonify(request.args))
    # print(dir(request))

    jobnumber=request.form['jobnumber']

    if jobnumber:
        print(jobnumber)

    

    print(request.method)
    if jobnumber and request.method == 'POST':
        if isjobnumber(jobnumber):
                print("existing")
                resp = jsonify(text=1)
                # resp.status_code = 200
                return resp

        else:
            print("NOT existing")
            resp = jsonify(text=0)
            # resp.status_code = 200
            return resp
    else:
        resp = jsonify(text=-1)
        # resp.status_code = 200
        return resp

  

@tinylib.route('/jobs', methods=['GET', 'POST'])
@login_required
def jobs_home():

    ##Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform= SearchSimple()
    if searchform.validate_on_submit() :
        searchstring=searchform.search.data
        session['search']=searchstring
        return redirect(url_for('tinylib.search',searchstring=searchstring,page=1, searchform=searchform ))


    jobs=Job.query.order_by(desc(Job.id))

    
    return render_template('tinylib/jobs.html', jobs=jobs,searchform=searchform)

@tinylib.route('/downloads', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def downloads():

    ##Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform= SearchSimple()
    if searchform.validate_on_submit() :
        searchstring=searchform.search.data
        session['search']=searchstring
        return redirect(url_for('tinylib.search',searchstring=searchstring,page=1, searchform=searchform ))
    
    return render_template('tinylib/downloads.html', searchform=searchform)

@tinylib.route('/jobapi/delete', methods=['GET','POST'])
def deletejob():
    
    request_data =request.values.get('jobnumber')
    print(request_data)
    request_data =request.values.get('id')
    print(request_data)
    request_data =request.values.get('description')
    print(request_data)
    request_data =request.values.get('customer')
    print(request_data)

    jobnumber=request.values.get('jobnumber')
    jobid=request.values.get('id')

    
    database_job=db.session.query(Job).filter(Job.id==jobid).first()
    if database_job:
        db.session.delete(database_job)
        db.session.commit() 
           


    return jsonify(request_data)

@tinylib.route('/jobapi/update', methods=['GET','POST'])
def updatejob():
    
    jobid=request.values.get('id')
    jobnumber=request.values.get('jobnumber')
    jobdescription=request.values.get('description')
    jobcustomer=request.values.get('customer')

    print (jobid,jobnumber,jobdescription,jobcustomer)

    database_job=db.session.query(Job).filter(Job.id==jobid).first()
    database_job.id=jobid
    database_job.jobnumber=jobnumber
    database_job.description=jobdescription
    database_job.customer=jobcustomer
    db.session.commit() 
           


    return jsonify("Success")


@tinylib.route('/jobdata', methods=['GET', 'POST'])
def data():
    jobs=Job.query.order_by(desc(Job.id))
    data=[]
    print("dsafad")
    for job in jobs:
        jobdict=job.__dict__
        #jobdict['user']=job.user.username
        # print(jobdict)

        jobdict.pop('_sa_instance_state')
        
        data.append(jobdict)

    return jsonify({"data":data})


@tinylib.route('/searchdata/<searchstring>', methods=['GET', 'POST'])
def searchdata(searchstring):
    args = json.loads(request.values.get("args"))
    columns = args.get("columns")

    ##Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform= SearchSimple()
    if searchform.validate_on_submit() :
        searchstring=searchform.search.data
        session['search']=searchstring
        return redirect(url_for('tinylib.search',searchstring=searchstring,page=1, searchform=searchform ))

    print(searchstring)
    search="%"+ searchstring+"%"

    results=Part.query.filter(or_(Part.description.like(search),
                                Part.partnumber.like(search))).order_by(Part.id.desc())
    data=[]
    print("dsafad")
    for part in results:
        part.updatefilespath(webfileserver)
        part.allprocesses=part.process + " "+part.process2 + " "+part.process3
        partdict=part.__dict__
        partdict.pop('_sa_instance_state')
        data.append(partdict)

    return jsonify({"data":data})




@tinylib.route('/s3/')
def entry_point():
    return 'Hello World!'

@tinylib.route('/s3/storage')
def storage():
    contents = list_files(bucket)
    return render_template('tinylib/s3storage.html', contents=contents)

@tinylib.route('/s3/upload', methods=['POST'])
def upload():
    if request.method == "POST":
        f = request.files['file']
        f.save(os.path.join(UPLOAD_FOLDER, f.filename))
        upload_file(f"uploads/{f.filename}", bucket)

        return redirect("/storage")

@tinylib.route('/s3/download/<folder>/<folder2>/<filename>', methods=['GET'])
def download(folder,folder2,filename):
    print(folder+"/"+folder2+"/"+filename)
    if request.method == 'GET':
        output = download_file(folder+"/"+folder2+"/"+filename, bucket)

        return send_file(output, as_attachment=True)


        
