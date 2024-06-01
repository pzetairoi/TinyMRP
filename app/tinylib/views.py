from sqlalchemy import or_, and_, not_, desc, asc
from wtforms import StringField, SubmitField, SelectField, TextAreaField, RadioField
from .publisher import BinderPDF, IndexPDF, bom_to_excel, get_files, get_all_files, \
      visual_list, label_list, loadexcelcompilelist, dictlist_to_excel
from .models import Part, Bom, solidbom, create_folder_ifnotexists, Job, Jobbom, deletepart
import copy
from operator import itemgetter
import pprint
from mongoengine.queryset.visitor import Q
from mongoengine import *
import pymongo
from flask_mongoengine.wtf import model_form
from .models import mongoPart, mongoJob, mongoSupplier, mongoOrder, \
    mongoBom, JSONEncoder, mongoToJson, Sandbox
from datetime import datetime, date
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
import re
from shutil import copyfile
import shutil
from pathlib import Path
import os
from sqlalchemy.sql import func
from sqlalchemy.sql import text
from .report import *
from .forms import *
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort
from flask import (
    Blueprint, flash, g, redirect, session,
    render_template, request, url_for, send_file,
    jsonify, after_this_request
)
from cmath import nan
from flask import jsonify, send_from_directory
from flask_login import login_required, current_user
from ..decorators import permission_required
import json


# To load the views
from . import tinylib
from ..main.forms import SearchSimple
from ..models import User, Permission
#from .awsbucket import upload_file, download_file, list_files


# Load app and configuration
# create config variables (to be cleaned in the future)

from flasky import db
from config import config as config_set 
from config import basedir


#To delete dowloaded files with a bit of a delay 
import threading
import time




config = config_set['tinymrp'].__dict__


# orint(config)

folderout = config['FOLDEROUT']
fileserver_path = config['FILESERVER_PATH']
datasheet_folder = config['DATASHEET_FOLDER']
deliverables_folder = config['DELIVERABLES_FOLDER']
variables_conf = config['VARIABLES_CONF']
webfileserver = config['WEBFILESERVER']
maincols = config['MAINCOLS']
refcols = config['REFCOLS']
deliverables = config['DELIVERABLES']
webserver = config['WEBSERVER']
process_conf = config['PROCESS_CONF']
lowercase_properties = config['LOWERCASE_PROPERTIES']
property_conf = config['PROPERTY_CONF']
bucket = config['BUCKET']


# For raw text queries on database


# Testing flask WTF to make forms easier


# Mongo engine stuff


client = pymongo.MongoClient("localhost", 27017)
mongodb = client.TinyMRP
partcol = mongodb["part"]
sandcol = mongodb['sandbox']
legend = config['PROCESS_LEGEND']

mongoPartForm = model_form(mongoPart)


# Setup for blueprint and pagination
bp = Blueprint('part', __name__)
pagination_items = 15

def zipfolderforweb(summaryfolder, delTempFiles=True, filepath_feedback=False):
        zipfile = Path(shutil.make_archive(Path(summaryfolder), 'zip', Path(summaryfolder)))
        #print("original " ,zipfile)

        path, filename = os.path.split(zipfile)
        finalfile = fileserver_path+deliverables_folder+"temp/"+filename
        #print("final " ,finalfile)

        if not os.path.isfile(finalfile):
            #print(zipfile)
            #print(finalfile)
            shutil.copy2(Path(zipfile), Path(finalfile))

        # Remove all the temp files
        os.remove(zipfile)
        if delTempFiles:
            shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

        # Create the web link
        weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

        #print(weblink)

        if filepath_feedback:
            return weblink, finalfile
        else:
            return weblink


def zipfileset(partlist, filelist, outputfolder="", zipfolder=True, delTempFiles=True):

    templist=[]
    #Get the list regardless if the items are mongoParts or dictionary:
    for part in partlist:
        if type(part)==dict:
            templist.append(mongoPart.objects(partnumber=part['partnumber'],revision=part['revision']).first())
        else:
            templist.append(part)
    partlist=templist


    #Add the missing attributes just in case:
    for part in partlist:
        for neededkey in  config['PROPERTY_CONF'].keys():
            if neededkey not in part.to_dict().keys() or part[neededkey]==None:
                part[neededkey]=""



    # Create export folder and alter the output folder and create it
    if outputfolder!="":
        summaryfolder=outputfolder
    else:
        # summaryfolder = os.getcwd()+"/temp/"+"datatablecompile" + \
        summaryfolder = "C:/TinyMRP/temp/"+"datatablecompile" + \
                    datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+"/"
    create_folder_ifnotexists(summaryfolder)

    fileset = []
    for filetype in config['FILES_CONF'].keys():
        if config['FILES_CONF'][filetype]['list'] == 'yes':
            refdict = config['FILES_CONF'][filetype]
            refdict['filetype'] = filetype
            #print(refdict)
            fileset.append(refdict)

    filepairs = []
    for filetype in fileset:
        
        if filetype['filetype'] in filelist:
            filetype['finalfolder']=summaryfolder+filetype['folder']+'/'
            create_folder_ifnotexists(filetype['finalfolder'])
            for i in range(6):
                extension = "extension"+str(i)
                # print(type(filetype[extension]))
                # print([filetype['filetype'],filetype['folder'],filetype[extension]])
                if filetype[extension] != "" and type(filetype[extension]) == str:
                    #print("YEAAAAH",filetype['filetype'], filetype['folder'], filetype[extension], filetype['filemod'],filetype['finalfolder'])
                    filepairs.append(
                        [filetype['filetype'], filetype['folder'], filetype[extension], filetype['filemod'],filetype['finalfolder']])

    print("filepairssssss", filepairs)

    # Loop over the fabrication components and create files
    for index, part in enumerate(partlist):
        filenamebit = part["partnumber"]+"_REV_"+part["revision"]

        for filetype, folder, extension, filemod,finalfolder in filepairs:
            sourcefile = fileserver_path+deliverables_folder + \
                folder+"/"+filenamebit+filemod+"."+extension
            
            if extension == 'dxf':
                targetfile = finalfolder+secure_filename(filenamebit+"-"+part["material"]+"_"+str(
                    part["thickness"])+"mm"+"_"+part["description"]+filemod+"."+extension)
                # print("thithithithithithithit")
                # print(part['thickness'])
                # print(part.to_dict())
                # print("thithithithithithithit")
            elif filetype == 'datasheet' and 'datasheet' in part.to_dict().keys():
                sourcefile = part['datasheet']
                extension_sourcefile = os.path.splitext(sourcefile)[-1]
                print(sourcefile)
                print("eoeoeoeoeoeoeoeoeoeooeoeoeoeoeo")

                if "."+extension == extension_sourcefile:
                    targetfile = finalfolder + \
                        secure_filename(
                            filenamebit+"_"+part["description"]+"_DATASHEET"+"."+extension)
                else:
                    next 

            else:
                try:
                    targetfile = finalfolder + \
                        secure_filename(filenamebit+"_" +
                                        part["description"]+filemod+"."+extension)
                    # print(targetfile)
                except:
                    #print("TARGETFILEERRROR",part)
                    pass

            if os.path.exists(sourcefile.replace(webfileserver, fileserver_path)):
                copyfile(sourcefile.replace(
                    webfileserver, fileserver_path), targetfile)
                # print(sourcefile,targetfile)
            else:
                #print("NOFILE - ", sourcefile)
                pass


    


    #Remove empty folders
    folders = list(os.walk(summaryfolder))[1:]

    for folder in folders:
        if not folder[2]:
            os.rmdir(folder[0])






    # Count files to avoid sending empty zip
    count = 0
    # print(summaryfolder)
    for root_dir, cur_dir, files in os.walk(summaryfolder):
        # print(files)
        count += len(files)
    #print("cocucocuoucoucouco", count)

    if count > 0:
        if zipfolder:
            weblink=zipfolderforweb(summaryfolder,delTempFiles=delTempFiles)
            # zipfile = Path(shutil.make_archive(
            #     Path(summaryfolder), 'zip', Path(summaryfolder)))
            # #print("original " ,zipfile)

            # path, filename = os.path.split(zipfile)
            # finalfile = fileserver_path+deliverables_folder+"temp/"+filename
            # #print("final " ,finalfile)

            # shutil.copy2(Path(zipfile), Path(finalfile))

            # # Remove all the temp files
            # os.remove(zipfile)
            # shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

            # # Create the web link
            # weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

            # print(weblink)

            return weblink
        else:
            return summaryfolder
    else:
        # shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)
        return ""

 
@tinylib.route('/custom/<filename>')
# @login_required
def serve_custom_file(filename):
    return send_from_directory(os.path.join(basedir, 'custom_files'), filename)
# return send_from_directory('custom_files', filename)

@tinylib.route('/api/listfileset', methods=('GET', 'POST'))
@login_required
def listfileset():
    datain = json.loads(request.values.get('alldata'))
    filelist = json.loads(request.values.get('filelist'))
    partlist = []

    for line in datain:
        partlist.append(mongoPart.objects(
            partnumber=line['partnumber'], revision=line['revision']).first())

    if len(partlist) > 0:
        return mongoToJson(zipfileset(partlist, filelist))
    else:
        return mongoToJson("")


@tinylib.route('/api/listvisual', methods=('GET', 'POST'))
@login_required
def listvisual():
    dictlist = json.loads(request.values.get('alldata'))
    # print(dictlist)

    # Clean image dict ref to local file
    for part in dictlist:
        # print("prere", part['pngpath'])
        part['pngpath'] = re.sub(r".*<img src='http://(.*)'.*", r"\1",
                                 part['pngpath']).replace(webfileserver, fileserver_path)
        if 'thumbnail' in part.keys():
            part['thumbnail'] = part['thumbnail'].replace(webfileserver, fileserver_path)
        # print("POSTre", part['pngpath'])

    if len(dictlist) > 0:
        return mongoToJson(visual_list(dictlist))
    else:
        return mongoToJson("")


@tinylib.route('/api/treepart', methods=('GET', 'POST'))
@login_required
def mongotreepartdata(partnumber="",revision="",depth='toplevel',web=True,consume='hide',structure='flat'):#,classified='show'):
    #print("*******************************************************************************************************")
    #print("*******************************************************************************************************")
    #print("*******************************************************************************************************")
    #print("** JOBNUMBER *",request.values.get('jobnumber'))
    #print("** ORDERNUMBER *",request.values.get('ordernumber'))
    #print("** JOBNUMBER *",request.values.get('jobnumber'))
    #print("*******************************************************************************************************")
    #print("*******************************************************************************************************")
    ##print("*******************************************************************************************************")
    ##print("*******************************************************************************************************")
    #print("*******************************************************************************************************")

    try:
        print(current_user._get_current_object())
    except:
        pass


    # Part tree filter
    try:
        rootnumber = request.values.get('rootnumber')
    except:
        rootnumber =""
    try:
        level = request.values.get('level')
    except:
        #print(" NO LEVEL ON PART DETAILS")
        level  =""
    try:
        processlist = json.loads(request.values.get('processlist'))
    except:
        #print("  NO PROCEWSS LIST")        
        processlist =[]
    try:
        consumed = request.values.get('consume')
    except:
        consumed  =""
    try:
        structured = request.values.get('structure')
    except:
        structured  =""
    try:      
        ordernumber = request.values.get('ordernumber')        
    except:
        ordernumber  =""        
    try:
        jobnumber = request.values.get('jobnumber')
    except:
        jobnumber  =""
    try:
        rootrevision = request.values.get('rootrevision')
    except:
        rootrevision  =""



        
    #print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    #print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    #print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    #print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    #print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    #print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    if revision == None or "%" in revision or revision == "":
        revision = ""
    else:
        revision = revision

        
     #Temporary dicts for storing outputs
    dictlist = []    
    

    #check if the entry preeference
        #First partnubmer in function
        #Second job
        #Third api partnubmer
    if partnumber!="":
        root = mongoPart.objects(
            partnumber=partnumber, revision=revision).first()
    else:
        job = mongoJob.objects(jobnumber=jobnumber).first()
        if job != None:
            root = mongoPart(partnumber=jobnumber, revision=jobnumber)

            for line in job.bom:
                root.bom.append(line)
                
        else:
            root = mongoPart.objects(
                partnumber=rootnumber, revision=rootrevision).first()  
    
    if root != None:
        allparts = mongoPart.objects(id__in=root.flatbomid())
    else:
        allparts = mongoPart.objects()







##################################################################
#####  USER BASED ACCESS APPLIED NOW FROM INITIAL FUNCTION FINDINGS
######################################################################
    #User access level and part filtering pre tasks
    #print("USER ACCESS LEVEL")
    if current_user._get_current_object().role_id>5:
        userid=str(current_user._get_current_object().id)
        userjobs=[]
        userparts=[]
        for job in mongoJob.objects():
            if userid in job.users:
                userjobs.append(job)
                userparts=userparts+job.fullbomid() 
        allparts = allparts(id__in=userparts)






    #Options from the api on the export
    if level == 'yes' or depth=='full':
        fulltree = True
    else:
        fulltree = False
    
    if consumed == 'yes' or consume=='show':
        consume = True
    else:
        consume = False

    # if classified == 'yes' or classified=='show' or classified=="" or classified=="only" or classified==None:
    #     show_classified = True
    # # if classified == 'only':
    # #     show_classified = 'only'
    # else:
    #     show_classified = False
        
  
    # print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    # print('structureD',structured)
    # print('structure',structure)
    # print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

    if structured == 'tree' or structure=='tree':
        structure = "tree"
    else:
        structure = 'flat'

    # print("sssssssssssssssssssssssssss")
    # print('structureD',structured)
    # print('structure',structure)
    # print("sssssssssssssssssssssssssss")



    if jobnumber!="":
        # Get all the ordered parts:
        joborders = mongoOrder.objects(job=jobnumber).all()
        totalorder = []
        totalsdict = {}
        
        for order in joborders:
            print(order)
            for bomline in order.bom:
                total = totalsdict.get(bomline.part, 0)+bomline.qty
                totalsdict[bomline.part] = total

        orderedlist = []
        
        for part in totalsdict.keys():
            orderedlist.append({'partnumber': part.partnumber,
                            'revision': part.revision, 'orderedqty': totalsdict[part]})

    
    
    # Get all teh components in a dictionary format
    if root!=None:
        dictlist = root.get_components(
                    bomdictlist=True, level="+", structure=structure, consume=consume, fulltree=fulltree)
        for x in dictlist:
            print(x['partnumber'],x['qty'],x['totalqty'])
    else:
        dictlist=mongoPart.objects()
    

    



    #Remove duplicates
    templist=[]
    partrevlist=[]
    for parto in dictlist:
        if parto['partnumber']+"_REV_"+parto['revision'] not in partrevlist:
            templist.append(parto)
            partrevlist.append(parto['partnumber']+"_REV_"+parto['revision'])
        
    dictlist=templist
    dictlist.sort(key=lambda item: item.get("partnumber"))
    for parto in dictlist:print(parto['partnumber'],parto['level'])    




    # Total records for the children
    recordsTotal = len(dictlist)
    # print("*******total*****", recordsTotal)
    # print("*******fulltree*****", fulltree)

    # Process filter
    # # if len(processlist>0):
    # allparts=allparts(process__in=processlist)

    # allparts=allparts(process__icontains=["machine","lasercut"])

    # Filter the process checkedboxes
    if processlist:
        reflist = []
        for partdict in dictlist:
            tolist = any(check in processlist for check in partdict['process'])
            

            if 'others' in processlist:
                tolist = tolist^any(check not in config['PROCESS_CONF'].keys() for check in partdict['process'])

            if tolist:
                reflist.append(partdict)

        dictlist = reflist

    
    # Global search filter
    # search = request.args.get('search[value]').lower()
    search = str(request.args.get('search[value]')).lower()
    # print("****************************************")
    # print("SEARCH?-",search,type(search))
    # print("****************************************")
    
    if search == "" or search==None or not search or search=='none':
        pass
    else:
        # print("SEARCH?-",search,type(search))
        dictlist = [x for x in dictlist if search in x['description'].lower(
        ) or search in x['partnumber'].lower()]

 
    

    # # SearchPanes
    searchpanes = {}

    # Cols search filter
    search = request.args.get('columns[0][search][value]')
    if search:
        if structure == "tree":
            dictlist = [x for x in dictlist if search.lower()
                        in x['level'].lower()]
        else:
            splitsearch = search.split(" ")
            for chunk in splitsearch:
                dictlist = [x for x in dictlist if chunk.lower(
                ) in '\t'.join(x['level']).lower()]

    search = request.args.get('columns[2][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower()
                        in x['partnumber'].lower()]
            # allparts=allparts(partnumber__icontains=chunk)

    search = request.args.get('columns[3][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower()
                        in x['revision'].lower()]

    search = request.args.get('columns[4][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower()
                        in x['description'].lower()]

    search = request.args.get('columns[5][search][value]')
    if search:
        splitsearch = search.split(" ")
        reflist = []
        for partdict in dictlist:
            tolist = False
            for chunk in splitsearch:
                for pro in partdict['process']:
                    tolist = tolist ^ (chunk.lower() in pro.lower())
            if tolist:
                reflist.append(partdict)
        dictlist = reflist

    search = request.args.get('columns[6][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower()
                        in x['finish'].lower()]

    search = request.args.get('columns[7][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower()
                        in x['material'].lower()]

    search = request.args.get('columns[11][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower()
                        in x['oem'].lower()]

    search = request.args.get('columns[12][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower(
            ) in x['oem_partnumber'].lower()]
    
    search = request.args.get('columns[13][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower(
            ) in x['classified'].lower()]

    # search = request.args.get('columns[14][search][value]')
    # if search:
    #     splitsearch = search.lstrip().rstrip().split(" ")
    #     cleansearch = [float(x) for x in splitsearch]
    #     # print(cleansearch)
    #     dictlist = [x for x in dictlist if x['thickness'] in cleansearch]

    search = request.args.get('columns[14][search][value]')
    if search:
        splitsearch = search.lstrip().rstrip().split(" ")
        splitsearch = [float(x) for x in splitsearch]
        maxval = max(splitsearch)
        minval = min(splitsearch)

        if maxval != minval:
            dictlist = [x for x in dictlist if x['mass']
                        >= minval and x['mass'] <= maxval]

        else:
            dictlist = [x for x in dictlist if x['mass'] >= minval]

    # Totalfiltered
    total_filtered = len(dictlist)

    

    # Col sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f'order[{i}][column]')

        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        # if col_name not in ['partnumber', 'description', 'process']:
        #     col_name = 'partnumber'

        descending = request.args.get(f'order[{i}][dir]') == 'desc'
        # col = getattr(Part, col_name)
        col = col_name

        order.append(col)
        i += 1
    if len(order) > 0:
        dictlist = sorted(dictlist, key=itemgetter(*order), reverse=descending)

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)

    if length!= None:
        if length > 0:
            # if search returns only one page
            if len(dictlist) <= length:
                # display only one page
                dictlist = dictlist[start:]
            else:
                limit = -len(dictlist) + start + length
                if limit < 0:
                    # display pagination
                    dictlist = dictlist[start:limit]
                else:
                    # display last page of pagination
                    dictlist = dictlist[start:]

    # Modify the imagelink if target is web and 
    # add missing attributes that are default
    # Account for ordered quantities

    for part in dictlist:

        #Add missing keys 
        for neededkey in  config['PROPERTY_CONF'].keys():
            
            if neededkey not in part.keys() or part[neededkey]==None:
                part[neededkey]=""
        
        #Image link loop
        if part['partnumber'] != None and web==True:
            if part['revision'] == "":
                urllink = url_for(
                    'tinylib.partnumber', partnumber=part['partnumber'], revision="%25")
            else:
                urllink = url_for(
                    'tinylib.partnumber', partnumber=part['partnumber'], revision=part['revision'])
            try:
                part['pngpath'] = '<a href="' + urllink + '">' + """<img src='""" + \
                    "http://"+ part['thumbnail'].replace(fileserver_path,webfileserver) + """' width=auto height=30rm></a>"""
            except:
                print(part)
                try:
                    part['pngpath'] = '<a href="' + urllink + '">' + """<img src='""" + \
                    "http://"+ part['pngpath'].replace(fileserver_path,webfileserver) +  """' width=auto height=30rm></a>"""
                except:
                    part['pngpath']= '<a href="' + urllink + '">' + """<img src='""" + \
                    "http://"+ webserver[:-6]+'/static/images/tinylogo.png' +  """' width=auto height=30rm></a>"""
        elif part['partnumber'] != None:
            pass

        else:
            # part['pngpath']=webfileserver+'/logo.png'
            part['pngpath']= webserver[:-6]+ url_for('static', filename='images/tinylogo.thumbnail.png')

                
                

            # Putting icons instead of text
            # iconhtml="<div>"
            # for i,icon in enumerate(part['process_icons']):
            #          iconhtml=iconhtml+  """<img src='""" + url_for('static', filename=icon) + """'  hspace=5 vspace=5  margin=0 height=auto width=25rm  >"""
            # part['process']=iconhtml+"</div>"
        
        #Account for the ordered parts for ORDERS
        # for part in dictlist:
        if jobnumber!="":
            for orderedpart in orderedlist:
                if part['partnumber'] == orderedpart['partnumber'] and part['revision'] == orderedpart['revision']:
                    part['orderedqty'] = orderedpart['orderedqty']

                #     part['remainingqty']=part['totalqty']
                #     part['orderedqty']=0
            if not 'orderedqty' in part.keys():
                part['orderedqty'] = 0
            part['remainingqty'] = part['totalqty'] - part['orderedqty']


    #Final output ready for datatables
    tabledata = {'data': dictlist,
                'recordsFiltered': total_filtered,
                'recordsTotal': recordsTotal,
                'draw': request.args.get('draw', type=int),
                'searchPanes': searchpanes,
                }
        # #print(tabledata)
        # #print(jsonify(tabledata))
    return mongoToJson(tabledata)


# Used functions

@tinylib.route('/api/part', methods=('GET', 'POST'))
@login_required
def mongopartdata():


    # Global search filter
    search = request.args.get('search[value]')

    # Job only filter
    jobnumber = request.values.get('jobnumber')
    ordernumber = request.values.get('ordernumber')
    onlyjob=request.values.get('onlyjob')
    # print(onlyjob)
    # print(ordernumber)

    # Part tree filter
    rootnumber = request.values.get('rootnumber')
    rootrevision = request.values.get('rootrevision')

    job = mongoJob.objects(jobnumber=jobnumber).first()
    order_in = mongoOrder.objects(ordernumber=ordernumber).first()
    # print(order_in)
    # print(order_in.to_dict())

    root = mongoPart.objects(partnumber=rootnumber,
                             revision=rootrevision).first()



    if order_in != None:
        allqtys=[]
        allids,allqtys =order_in.flatbomid(qty=True)
        allparts = mongoPart.objects(id__in=allids)
        for part,qty in zip(allparts,allqtys):
            part['qty']=qty
            # print(part.to_dict())



    elif job != None and onlyjob!="no":
        allparts = mongoPart.objects(id__in=job.flatbomid())
        if order_in != None:
                    allqtys=[]
                    allids,allqtys =order_in.flatbomid(qty=True)
                    allparts = mongoPart.objects(id__in=allids)
                    for part,qty in zip(allparts,allqtys):
                        part['qty']=qty
    elif root != None:
        allparts = mongoPart.objects(id__in=root.flatbomid())
    else:
        allparts = mongoPart.objects()

    


    # Total records for the children
    recordsTotal = allparts.count()
    # print(recordsTotal)

    if search == "" or not search:
        pass
    else:
        allparts = allparts(Q(description__icontains=search)
                            | Q(partnumber__icontains=search))



##################################################################
#####  USER BASED ACCESS APPLIED NOW FROM INITIAL FUNCTION FINDINGS
######################################################################
    #User access level and part filtering pre tasks
    print("USER ACCESS LEVEL")
    print(current_user._get_current_object().role_id)
    print(type(current_user._get_current_object().role_id))
    if current_user._get_current_object().role_id>5:
    
        userid=str(current_user._get_current_object().id)
        userjobs=[]
        userparts=[]
        for job in mongoJob.objects():
            if userid in job.users:
                userjobs.append(job)
                userparts=userparts+job.fullbomid() 
        allparts = allparts(id__in=userparts)



    # # SearchPanes
    searchpanes = {}

    # Cols search filter
    search = request.args.get('columns[1][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(partnumber__icontains=chunk)

    search = request.args.get('columns[2][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(revision__icontains=chunk)

    search = request.args.get('columns[3][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(description__icontains=chunk)

    search = request.args.get('columns[4][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(process__icontains=chunk)

    search = request.args.get('columns[5][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(finish__icontains=chunk)

    search = request.args.get('columns[6][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(material__icontains=chunk)

    search = request.args.get('columns[8][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(oem__icontains=chunk)

    search = request.args.get('columns[9][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(oem_partnumber__icontains=chunk)

    search = request.args.get('columns[10][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(classified__icontains=chunk)

    search = request.args.get('columns[11][search][value]')
    if search:
        splitsearch = search.lstrip().rstrip().split(" ")
        splitsearch = [float(x) for x in splitsearch]
        maxval = max(splitsearch)
        minval = min(splitsearch)

        if order_in != None:
            if maxval != minval:
                allparts = allparts(qty__gte=minval)
                allparts = allparts(qty__lte=maxval)
            else:
                allparts = allparts(qty__gte=minval)
            
        else:
            if maxval != minval:
                allparts = allparts(mass__gte=minval)
                allparts = allparts(mass__lte=maxval)
            else:
                allparts = allparts(mass__gte=minval)




    # search = request.args.get('columns[11][search][value]')
    # if search:
    #     splitsearch = search.lstrip().rstrip().split(" ")
    #     splitsearch = [float(x) for x in splitsearch]
    #     maxval = max(splitsearch)
    #     minval = min(splitsearch)

    #     if maxval != minval:
    #         allparts = allparts(mass__gte=minval)
    #         allparts = allparts(mass__lte=maxval)
    #     else:
    #         allparts = allparts(mass__gte=minval)            

    # All filtered parts
    total_filtered = allparts.count()
    # print(total_filtered)
    #print("All parts ", total_filtered)
    allparts = allparts.order_by("-id")





    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f'order[{i}][column]')

        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        # if col_name not in ['partnumber', 'description', 'process']:
        #     col_name = 'partnumber'

        descending = request.args.get(f'order[{i}][dir]') == 'desc'
        # col = getattr(Part, col_name)
        col = col_name
        if descending:
            col = "-"+col

        order.append(col)
        i += 1
    if len(order) > 0:
        # query = query.order_by(*order)
        # print(order)
        allparts = allparts.order_by(*order)

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)

    # #print("Start ",start," - length ",length)

    # if start==None: start=20
    # if length==None: length=50

    #print("Start ",start," - length ",length)

    # query = query.offset(start).limit(length)
    # allparts=allparts.skip(start).limit(length)
    paginatedparts = allparts.skip(start).limit(length)

    #print("Paginated parts ", allparts.count())

    # check files and save (to polish redundant checks)
    # for part in paginatedparts:

    #     part.getweblinks()

    if order_in!= None: 
        allids,allqtys =order_in.flatbomid(qty=True)
        
    

    # Modify the imagelink
    webdata = []
    for part in paginatedparts:
        
        part.updateFileset(web=True)
        
        if order_in!= None: 
            for id,qty in zip(allids,allqtys):
                if id==part.id:
                    
                    # print(part['qty'],part)
                    print(part)
        else:
            part['qty']=0


            
        

        #Add the missing attributes just in case:
    
        for neededkey in  config['PROPERTY_CONF'].keys():
            if neededkey not in part._fields.keys() or part[neededkey]==None:
                part[neededkey]=""

        if part.partnumber != None:
            if part.revision == "":
                urllink = url_for(
                    'tinylib.partnumber', partnumber=part.partnumber, revision="%25")
                # #print(urllink)
            else:
                # print(part.partnumber)
                urllink = url_for(
                    'tinylib.partnumber', partnumber=part.partnumber, revision=part.revision)
                # #print("the part link" , urllink)

            try:
                part['pngpath'] = '<a href="' + urllink + '">' + """<img src='""" + \
                    "http://"+part.thumbnail + """' width=auto height=30rm></a>"""
                # #print("the image link" , part['pngpath'])
            except:
                part['pngpath'] = '<a href="' + urllink + '">' + """<img src='""" + \
                    "http://"+part.pngpath + """' width=auto height=30rm></a>"""

            partdict = part.to_dict()

            if job != None:
                for bom in job.bom:

                    if part.id == bom.part.id:
                        partdict['qty'] = bom.qty

            webdata.append(partdict)

    tabledata = {'data': webdata,
                 'recordsFiltered': total_filtered,
                 'recordsTotal': recordsTotal,
                 'draw': request.args.get('draw', type=int),
                 'searchPanes': searchpanes,

                 }
    # #print(tabledata)
    #print("eeoeoeoeooeoeoeo")
    #print(tabledata)
    #print("eeoeoeoeooeoeoeo")
    return mongoToJson(tabledata)


@tinylib.route('/api/oldpart', methods=('GET', 'POST'))
@login_required
def partdata():

    query = Part.query

    # Global search filter
    search = request.args.get('search[value]')
    search = 'bean'

    if search:
        query = query.filter(db.or_(
            Part.partnumber.like(f'%{search}%'),
            Part.description.like(f'%{search}%')
        ))

    # Cols search filter
    search = request.args.get('columns[1][search][value]')
    if search:
        query = query.filter(Part.partnumber.like(f'%{search}%'))
    search = request.args.get('columns[2][search][value]')
    if search:
        query = query.filter(Part.revision.like(f'%{search}%'))
    search = request.args.get('columns[3][search][value]')
    if search:
        query = query.filter(Part.description.like(f'%{search}%'))
    search = request.args.get('columns[4][search][value]')
    if search:
        query = query.filter(Part.process.like(f'%{search}%'))
    search = request.args.get('columns[5][search][value]')
    if search:
        query = query.filter(Part.process2.like(f'%{search}%'))
    search = request.args.get('columns[6][search][value]')
    if search:
        query = query.filter(Part.process3.like(f'%{search}%'))
    search = request.args.get('columns[7][search][value]')
    if search:
        query = query.filter(Part.finish.like(f'%{search}%'))

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

    tabledata = {'data': [part.to_dict() for part in query],
                 'recordsFiltered': total_filtered,
                 'recordsTotal': query.count(),
                 'draw': request.args.get('draw', type=int),
                 }

    # print(tabledata)
    # response
    return jsonify(tabledata)


@tinylib.route('/inventory', methods=('GET', 'POST'))
@login_required
def allparts():

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        # flash(searchstring)
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))
    else:
        if 'search' in session.keys():
            searchstring = session['search']

        # flash("else"+searchstring)

    # print(config['FILES_CONF'])
    # fileset=[]
    # for filetype in config['FILES_CONF'].keys():
    #     if config['FILES_CONF'][filetype]['list']=='yes':
    #         refdict=config['FILES_CONF'][filetype]
    #         refdict['filetype']=filetype
    #         fileset.append(refdict)

    return render_template('tinylib/part/inventory.html', title="Part list", searchform=searchform, legend=config['PROCESS_LEGEND'], fileset=config['FILESET'])


@tinylib.route('/part/search', methods=('GET', 'POST'))
@login_required
def search(searchstring="", page=1):
    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        # flash(searchstring)
        session['search'] = searchstring.rstrip().lstrip()
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))
    else:
        searchstring = session['search'].rstrip().lstrip()
        # flash("else"+searchstring)

    fileset = []
    for filetype in config['FILES_CONF'].keys():
        if config['FILES_CONF'][filetype]['list'] == 'yes':
            refdict = config['FILES_CONF'][filetype]
            refdict['filetype'] = filetype
            fileset.append(refdict)

    return render_template('tinylib/part/inventory.html', title="Search results",
                           searchform=searchform, searchstring=searchstring, legend=config['PROCESS_LEGEND'], fileset=config['FILESET'])


@tinylib.route('/part/create', methods=('GET', 'POST'))
@login_required
def create():
    searchform = SearchSimple()
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
                (partnumber, revision, description)
            )
            db.commit()
            return redirect(url_for('tinylib.index'))

    return render_template('part/create.html')

# Detail valid inputs: "quick" and "full"
@tinylib.route('/part/detail/<partnumber>:', methods=('GET', 'POST'))
@login_required
def partnumbernorev(partnumber):
    return redirect(url_for('tinylib.partnumber',partnumber=partnumber,revision="%25"))

# Detail valid inputs: "quick" and "full"
@tinylib.route('/part/detail/<partnumber>:<revision>', methods=('GET', 'POST'))
@login_required
# @tinylib.route('/part/<partnumber>_rev_<revision>/page/<int:page>', methods=('GET', 'POST'))
def partnumber(partnumber, revision):

    
    


    treedata = {}
    commentform = PartComment()
    searchform = SearchSimple()
    compileform = Compile()

    rev=revision.lstrip().rstrip()

    if rev == None or rev == "%" or rev == "%25" or rev == "":
        rev = ""
    else:
        rev = revision
 
    if request.method == 'GET':

        
        part = mongoPart.objects(partnumber=partnumber, revision=rev).first()



        ##################################################################
#####  USER BASED ACCESS APPLIED NOW FROM INITIAL FUNCTION FINDINGS
######################################################################
    #User access level and part filtering pre tasks
        #print("USER ACCESS LEVEL")
        if current_user._get_current_object().role_id>5:
            
            userid=str(current_user._get_current_object().id)
            userjobs=[]
            userparts=[]
            for job in mongoJob.objects():
                if userid in job.users:
                    userjobs.append(job)
                    userparts=userparts+job.fullbomid() 
            if part.id not in userparts:
                return "USER HAS NO ACCESS TO THIS PART DETAILS CHECK WITH ADMIN"
            
            






        parts = part.children_with_qty()




        

        # print(part.get_components(bomdictlist=True))
        # print(part.to_dict())

        hardware = []
        composed = []
        composedicons = []
        composedprocesses = []

        # UPdate related part files location to the webserver
        part.updateFileset(web=True, persist=True)
        part.get_process_icons()

        legend = config['PROCESS_LEGEND']
        needed_processes = []
        icons = []
        colors = []

        # Get all processes for legend and export options
        flatbomid = part.flatbomid(toplevelonly=False)
        flatbomid.append(part.id)
        bom_processes = mongoPart.objects(id__in=flatbomid).distinct('process')

        for process in bom_processes:
            if process in process_conf.keys():
                needed_processes.append(process)
            elif "others" not in needed_processes and process != "":
                needed_processes.append("others")

        # To get the top level flatbom and having better resolution from them
        # due to the updatefilespath function affection all the parts (database object)
        for parto in parts:
            if "hardware" in parto['process']:
                hardware.append(parto)
            else:

                # parto.updatefilespath(webfileserver)
                parto.updateFileset(web=True)

                for process in process_conf.keys():
                    if parto.hasProcess(process) and process not in needed_processes:
                        needed_processes.append(process)
        # print(needed_processes)

        for parto in hardware:
            parts.remove(parto)

        parents = part.parents_with_qty()
 
        for parto in parents:
            parto.updateFileset(web=True)
            

        for process in needed_processes:
            try:
                icons.append(process_conf[process]['icon'])
                colors.append(process_conf[process]['color'])
            except:
                #print("No icon for ", process)
                pass

        legend = [{'process': process, 'icon': 'images/'+icon, 'color': color}
                  for (process, icon, color) in zip(needed_processes, icons, colors)]

        part.updateFileset(web=True)

        

        #Modify the compile form with the processes and files
        compileform.category.choices=[('improvement','improvement'),('mistaaaaake','mistaaaaaaake'),('procurement','procurement')]
        compileform.processes.choices=list(zip(needed_processes,needed_processes))
        compileform.files.choices=list(zip(list(config['FILES_CONF'].keys()),list(config['FILES_CONF'].keys())))

        return render_template("tinylib/part/details3D.html", part=part, parts=parts, treedata=treedata,
                               hardware=hardware, parents=parents,
                               commentform=commentform,
                               # pagination="",
                               #    comments=comments,
                               legend=legend, title=part.partnumber, processes=needed_processes,
                               composed=composed, composedprocesses=composedprocesses, searchform=searchform,
                               compileform =compileform, allfiles=config['ALLFILES'],
                               fileset=config['FILESET'])

    if request.method == 'POST':
        if 'search' in request.form:
            if request.form['search'] != "":
                search = request.form['search']
                session['search'] = search.lstrip().rstrip()
                return redirect(url_for('tinylib.search', searchstring=search,   compileform =compileform,
                 searchform=searchform,  legend=config['PROCESS_LEGEND']))
 

@tinylib.route('/part/uploader', methods=['GET', 'POST'])
@login_required
def upload_file():
    bomform = UploadForm()
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    if bomform.validate_on_submit():

        f = secure_filename(bomform.file.data.filename)
        f=bomform.file.data.filename
        targetfolder = os.path.dirname(os.path.abspath(
            __file__)) + "/" + config['UPLOAD_PATH'] + "/"

        targetfolder=fileserver_path+deliverables_folder+"temp/"+ "/" + config['UPLOAD_PATH'] + "/"
        targetfile = targetfolder + f
        filestring = Path(targetfile).stem

        # Save uploaded file
        # bomform.file.data.save('/tmp/tsest.zip')
        # bomform.file.data.save('/home/tinymrp/teasdfsat.zip')
        # bomform.file.data.save('/home/tinymrp/Shared/Deliverables/temp/upload/asdtesat.zip')
        # shutil.unpack_archive('/home/tinymrp/Shared/Deliverables/temp/upload/asdtesat.zip', targetfolder, "zip")
        
        # bomform.file.data.save('/tmp/tsest.zip')
        bomform.file.data.save(Path(targetfile))

        # unzip file
        shutil.unpack_archive(targetfile, targetfolder, "zip")

        bomfolder = targetfolder+"/"+filestring
        bomfile = bomfolder+"/"+filestring+"_TREEBOM.txt"
        flatfile = bomfolder+"/"+filestring+"_FLATBOM.txt"


        # Create the SOLIDBOM
        bom_in = solidbom(bomfile, flatfile,
                          deliverables_folder, fileserver_path+folderout)


        
        # Remove uploaded files and temp dirs
        try:
            os.remove(targetfile)
            os.remove(bomfile)
            os.remove(flatfile)
            shutil.rmtree(bomfolder)

            #print("NOTERASED")
        except:
            flash("Couldn't erase upload file ", targetfile)

        session['search'] = bom_in.partnumber

        # #print(input("error"))
        # return render_template('tinylib/upload.html',upload=False, searchform=searchform , bomform=bomform)
        return redirect(url_for('tinylib.search', searchstring=bom_in.partnumber, page=1, searchform=searchform))

        # Remove solidbomb splitfiles
        # try:
        #     shutil.rmtree(bomfolder)
        #     # os.remove(flatfile)
        #     # os.remove(bomfile)
        # except:
        #     flash("Couldn't temp bom/flat files ", bomfile,flatfile)

        # return jsonify(bom_in.partnumber)

        # if bom_in.revision=="":
        #     bom_in.revision="%25"

        # flash("BOM uploaded successfully")
        # # return render_template('tinylib/upload.html',upload=True, searchform=searchform , bomform=bomform)

        # if bom_in.revision=="":
        #     bom_in.revision="%25"

        # return redirect(url_for('tinylib.details',partnumber=bom_in.partnumber,revision=bom_in.revision, searchform=searchform ))
 
    else:
        return render_template('tinylib/upload.html', upload=False, searchform=searchform, bomform=bomform)


@tinylib.route('/part/excelcompile', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.COMPILE)
def excelcompile():
    weblink = False
    excelform = UploadForm()
    searchform = SearchSimple()

    if searchform.validate_on_submit():
        page = 1
        search = "%" + searchform.search.data+"%"
        searchstring = searchform.search.data
        # print(search)
        error = None

        if not search:
            error = 'A text string required'

        if error is not None:
            flash(error)
        else:
            # print(search,search)

            allparts = Part.query.filter(or_(Part.description.like(search),
                                             Part.partnumber.like(search))).order_by(Part.partnumber.desc())

            if 'rev' in request.form:
                allparts = allparts.filter(Part.revision != "")
            if 'assy' in request.form:
                allparts = allparts.filter(or_(Part.process == "assembly"))
            pagination = allparts.paginate(page, per_page=pagination_items,
                                           error_out=False)
            parts = pagination.items
            for part in parts:
                part.updatefilespath(webfileserver, png_thumbnail=True)
            session['search'] = searchstring
            # print(search,search,search)
            return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    if excelform.validate_on_submit():
        f = secure_filename(excelform.file.data.filename)

        #print("in post")
        # f = request.files['file']
        folder = os.path.dirname(os.path.abspath(__file__))
        folder=fileserver_path+deliverables_folder+"temp/"

        targetfile = folder + "/" + \
            config['UPLOAD_PATH'] + "/" + secure_filename(f)
        # print(targetfile)

        try:
            os.remove(targetfile)
        except:
            pass
        excelform.file.data.save(targetfile)

        # print(folderout)
        flatbom, part_dict_list = loadexcelcompilelist(
            targetfile, export_objects=True)
        # print(flatbom)

        flash("Excel file uploaded successfully")

        # Create export folder and alter the output folder and create it
        summaryfolder = fileserver_path+deliverables_folder+"/temp/"+"excelcompile" + \
            datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+"/"
        create_folder_ifnotexists(summaryfolder) 
 

        pdf_pack = BinderPDF( part_dict_list, outputfolder=summaryfolder,savevisual=True)

        # Copy original excel file to export folder
        shutil.copy2(Path(targetfile), Path(summaryfolder+"inputfile" +
                     datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+".xlsx"))

        # Get all files of the flatbom
        
        zipfileset(part_dict_list, ['pdf', 'dxf', 'step','datasheet'],outputfolder=summaryfolder, delTempFiles=False)

        # Compile all in a zip file
        zipfile = Path(shutil.make_archive(
            Path(summaryfolder), 'zip', Path(summaryfolder)))
        #print("original " ,zipfile)

        path, filename = os.path.split(zipfile)
        finalfile = fileserver_path+deliverables_folder+"temp/"+filename
        #print("final " ,finalfile)

        if not os.path.samefile(zipfile,finalfile):
            shutil.copy2(Path(zipfile), Path(finalfile))

      

        # Create the web link
        weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)
        # weblink=weblink.replace(" ", "%20")

        # Remove all the temp files
        try:
            os.remove(targetfile)
            shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)
        except:
            #print("Couldn't erase upload file ", targetfile)
            flash("Couldn't erase upload file ", targetfile)
            print(targetfile)

        return render_template('tinylib/excelcompile.html', excelform=excelform, upload=True, weblink=weblink, filepath=filename, searchform=searchform)

    else:
        return render_template('tinylib/excelcompile.html', excelform=excelform, upload=False, weblink=False, filepath=False, searchform=searchform)


@tinylib.route('/part/<partnumber>_rev_<revision>/drawingpack/<components_only>', methods=('GET', 'POST'))
@login_required
def drawingpack(partnumber, revision, components_only="NO"):

    components_only = request.args.get(
        'components_only', default='*', type=str)

    if components_only == "YES":
        components_only = True
    elif components_only == "NO": 
        components_only = False
    else:
        components_only = False

    if revision == None or "%" in revision or revision == "":
        rev = ""
    else:
        rev = revision 

    # Get the top part level object
    part = mongoPart.objects(partnumber=partnumber, revision=rev).first()
    # Set qty to one to compute the rest
    part.qty = 1
 
    flatbom =part.get_components(bomdictlist=True, level="+", structure="flat", consume=False, fulltree=True)
    # print(flatbom)

    # summaryfolder = os.getcwd()+"/temp/"+part.get_tag()+"/"
    summaryfolder = "C:/TinyMRP/temp/"+part.get_tag()+"/"
    bomtitle = "-manufacturing list-"
    create_folder_ifnotexists(summaryfolder)

 
    pdf_pack = BinderPDF(flatbom, outputfolder=summaryfolder)
    # print(pdf_pack)

    path, filename = os.path.split(pdf_pack)
    finalfile = fileserver_path+deliverables_folder+"temp/"+filename

    shutil.move(pdf_pack, finalfile)

    finalfile = finalfile.replace(fileserver_path, webfileserver)
    # print(finalfile)
    # print("changes?")

    return redirect("http://"+finalfile)


@tinylib.route('/part/<partnumber>_rev_<revision>/fabrication', methods=('GET', 'POST'))
@login_required
def fabrication(partnumber, revision):
    if revision == None or "%" in revision or revision == "":
        rev = ""
    else:
        rev = revision

    # Get the top part level object
    part_in = Part.query.filter_by(partnumber=partnumber, revision=rev).first()
    # print(part_in)
    # Set qty to one to compute the rest and updatepaths
    part_in.qty = 1
    part_in.updatefilespath(fileserver_path, local=True)

    # Add the top part to the list
    flatbom = []
    flatbom.append(part_in)
    flatbom = flatbom+part_in.get_components(components_only=False)

    # Extract the welding components
    if part_in.hasProcess("welding"):
        manbom = []
        manbom.append(part_in)
    else:
        manbom = [x for x in flatbom if x.hasProcess("welding")]

    if len(manbom) == 0 and part_in.hasProcess("welding"):
        manbom.append(part_in)
    elif len(manbom) == 0:
        return "NO FABRICATION AVAILABLE IN THE PARTNUMBER"

    # Create export folder and alter the output folder and create it
    #summaryfolder = os.getcwd()+"/temp/"+part_in.tag+"-fabrication_pack/"
    summaryfolder = "C:/TinyMRP/temp/"+part_in.tag+"-fabrication_pack/"
    create_folder_ifnotexists(summaryfolder)

    # Create the SolidBom class object for easier referencing, and override the output folder
    bom_in = solidbom.solidbom_from_flatbom(manbom, part_in)
    bom_in.folderout = summaryfolder

    # Create list with title
    bomtitle = bom_in.tag+"- scope of supply"
    excel_list = bom_to_excel(
        bom_in.flatbom, bom_in.folderout, title=bomtitle, qty="qty", firstrow=1)

    # Copy root part image and drawing
    path, filename = os.path.split(part_in.pngpath)
    copyfile(part_in.pngpath, summaryfolder+filename)

    # Machined parts used in fabrication
    machined = []

    # Loop over the fabrication components and create files
    for index, component in enumerate(manbom):

        # Get flatbom for each component
        com_flatbom = []
        com_flatbom.append(component)
        com_flatbom = com_flatbom + \
            component.get_components(components_only=False)

        # Get the machined components:
        # for mach_comp in com_flatbom:
        #    if mach_comp.hasProcess("machine"):
        #        machined.append(mach_comp)

        # Create the flatbom for each man item and alter the output folder and create it
        com_bom = solidbom.solidbom_from_flatbom(com_flatbom, component)
        com_bom.folderout = summaryfolder+com_bom.partnumber+"/"
        create_folder_ifnotexists(com_bom.folderout)

        # Create the drawing pack (pdf)
        com_dwgpack = IndexPDF(
            com_bom, outputfolder=com_bom.folderout, sort=False)

        # Get manufacturing files
        get_files(com_bom.flatbom, 'dxf', com_bom.folderout)
        get_files(com_bom.flatbom, 'step', com_bom.folderout)
        get_files(com_bom.flatbom, 'pdf', com_bom.folderout)
        get_files(com_bom.flatbom, 'png', com_bom.folderout)

        # Create the bom title
        bomtitle = com_bom.tag+"-components list"

        # Crete excelist
        excel_list = bom_to_excel(
            com_bom.flatbom, com_bom.folderout, title=bomtitle, qty="qty")

        # print(com_bom.folderout)
        com_dwgpack = IndexPDF(
            com_bom, outputfolder=com_bom.folderout, sort=False)
        # print(com_dwgpack)

    zipfile = Path(shutil.make_archive(
        Path(summaryfolder), 'zip', Path(summaryfolder)))
    #print("original " ,zipfile)

    path, filename = os.path.split(zipfile)
    finalfile = fileserver_path+deliverables_folder+"temp/"+filename
    #print("final " ,finalfile)

    shutil.copy2(Path(zipfile), Path(finalfile))

    # Remove all the temp files
    os.remove(zipfile)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    # Create the web link
    weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

    return redirect(weblink)


@tinylib.route('/part/<partnumber>_rev_<revision>/<processin>_componentsonly_<components_only>', methods=('GET', 'POST'))
@login_required
def process_docpack(partnumber, revision, processin, components_only):

    # Remove spaces from link
    process = processin.replace('%20', ' ')

    if revision == None or "%" in revision or revision == "":
        rev = ""
    else:
        rev = revision

    # Get the top part level object
    part_in = Part.query.filter_by(partnumber=partnumber, revision=rev).first()
    # print(part_in)
    # Set qty to one to compute the rest and updatepaths
    part_in.qty = 1
    part_in.updatefilespath(fileserver_path, local=True)

    # Add the top part to the list
    flatbom = []
    flatbom.append(part_in)

    # Check if needed to consume the welded components or not
    if components_only == "YES":
        flatbom = flatbom+part_in.get_components(components_only=True)

    else:
        flatbom = flatbom+part_in.get_components(components_only=False)

    # Extract the process related components components
    part_in.MainProcess()
    # if part_in.hasProcess(process):
    if part_in.isMainProcess(process):
        manbom = []
        manbom.append(part_in)
    elif components_only == "YES":
        manbom = [x for x in flatbom if x.MainProcess() == process]
    else:
        manbom = [x for x in flatbom if x.isMainProcess(process)]

    if len(manbom) == 0 and part_in.isMainProcess(process):
        manbom.append(part_in)
    elif len(manbom) == 0:
        return ("NO COMPONENTS WITH THE PROCESS " + process.upper())

    # Create export folder and alter the output folder and create it
    # summaryfolder = os.getcwd()+ "/temp/"+part_in.tag+"-"+process.upper() + \
    summaryfolder = "C:/TinyMRP/temp/"+part_in.tag+"-"+process.upper() + \
        "-components_only_"+components_only + "_pack/"
    create_folder_ifnotexists(summaryfolder)

    # Create the SolidBom class object for easier referencing, and override the output folder
    bom_in = solidbom.solidbom_from_flatbom(manbom, part_in)
    bom_in.folderout = summaryfolder

    # Create list with title
    bomtitle = bom_in.tag+"- scope of supply"
    #excel_list=bom_to_excel(bom_in.flatbom,bom_in.folderout,title=bomtitle,qty="qty", firstrow=1)
    excel_list = bom_in.solidbom_to_excel(process=processin)

    # Copy root part image and drawing
    path, filename = os.path.split(part_in.pngpath)
    copyfile(part_in.pngpath, summaryfolder+filename)

    # Get manufacturing files
    if process == "machine" or process == "folding" or process == "profile cut" or process == "3d laser" or process == "3d print" or process == "rolling":
        get_files(bom_in.flatbom, 'step', summaryfolder)

    if process != "hardware":
        get_files(bom_in.flatbom, 'png', summaryfolder)

    if process == "lasercut" or process == "folding" or process == "machine" or process == "profile cut":
        get_files(bom_in.flatbom, 'dxf', summaryfolder)

    get_files(bom_in.flatbom, 'pdf', summaryfolder)

    # Compile all in a zip file
    zipfile = Path(shutil.make_archive(
        Path(summaryfolder), 'zip', Path(summaryfolder)))
    #print("original " ,zipfile)

    path, filename = os.path.split(zipfile)
    finalfile = fileserver_path+deliverables_folder+"temp/"+filename
    #print("final " ,finalfile)

    shutil.copy2(Path(zipfile), Path(finalfile))

    # Remove all the temp files
    os.remove(zipfile)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    # Create the web link
    weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

    return redirect(weblink)


@tinylib.route('/part/<partnumber>_rev_<revision>/<processin>_<components_only>', methods=('GET', 'POST'))
@login_required
def process_visuallist(partnumber, revision, processin, components_only):

    # Remove spaces from link
    process = processin.replace('%20', ' ')

    rev = ""
    if revision == None or revision == "%" or revision == "" or revision == "%25" or revision == "%2525":
        rev = ""
    else:
        rev = revision

    # Get the top part level object
    part_in = mongoPart.objects(partnumber=partnumber, revision=rev).first()

    # print(part_in)
    # Set qty to one to compute the rest and updatepaths
    part_in['qty'] = 1
    part_in.updateFileset(fileserver_path)

    # Add the top part to the list
    flatbom = []
    flatbom.append(part_in)

    # Check if needed to consume the welded components or not
    if components_only == "YES":
        flatbom = flatbom+part_in.get_components(components_only=True)

    else:
        flatbom = flatbom+part_in.get_components(components_only=False)

    # Extract the process related components components
    part_in.MainProcess()
    if part_in.hasProcess(process):
        manbom = []
        manbom.append(part_in)
    elif process == "toplevel":
        manbom = [x for x in part_in.children if not x.hasProcess("hardware")]
    elif process == "all":
        manbom = [x for x in flatbom if not x.hasProcess("hardware")]
        # Sort the list by process
        manbom = sorted(manbom, key=lambda x: x.partnumber, reverse=False)
        manbom = sorted(manbom, key=lambda x: x.process, reverse=False)
    elif components_only == "YES":
        manbom = [x for x in flatbom if x.MainProcess() == process]
    else:
        manbom = [x for x in flatbom if x.isMainProcess(process)]

    if len(manbom) == 0 and part_in.isMainProcess(process):
        manbom.append(part_in)
    elif len(manbom) == 0:
        return ("NO COMPONENTS WITH THE PROCESS " + process.upper())

    # Create export folder and alter the output folder and create it
    # summaryfolder = os.getcwd()+ "/temp/"+part_in.tag+"-"+process.upper() + "_pack/"
    summaryfolder = "C:/TinyMRP/temp/"+part_in.tag+"-"+process.upper() + "_pack/"
    create_folder_ifnotexists(summaryfolder)

    # Create the SolidBom class object for easier referencing, and override the output folder
    bom_in = solidbom.solidbom_from_flatbom(manbom, part_in)
    bom_in.folderout = summaryfolder

    # Assign title
    if process == "toplevel":
        visualtitle = "Top level components"
    else:
        visualtitle = "Visual_summary_components_only-"+components_only + "-"+process

    # Create the visual list
    visuallist = visual_list(
        bom_in, outputfolder=summaryfolder, title=visualtitle.replace(" ", "_"))

    # MOVE FILE to temp folder
    path, filename = os.path.split(visuallist)
    finalfile = fileserver_path+deliverables_folder+"temp/"+filename

    shutil.copy2(Path(visuallist), Path(finalfile))

    # Remove all the temp files
    os.remove(visuallist)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    # Create the web link
    weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

    # print(weblink)

    return redirect(weblink)


@tinylib.route('/part/<partnumber>_rev_<revision>/flatbom/<components_only>', methods=('GET', 'POST'))
@login_required
def flatbom(partnumber, revision, components_only):

    if revision == None or "%" in revision or revision == "":
        rev = ""
    else:
        rev = revision

    # Get the top part level object
    part_in = Part.query.filter_by(partnumber=partnumber, revision=rev).first()
    # print(part_in)
    # Set qty to one to compute the rest and updatepaths
    part_in.qty = 1
    part_in.updatefilespath(fileserver_path, local=True)

    # Add the top part to the list
    flatbom = []
    flatbom.append(part_in)

    # Check if needed to consume the welded components or not
    if components_only == "YES":
        flatbom = flatbom+part_in.get_components(components_only=True)

    else:
        flatbom = flatbom+part_in.get_components(components_only=False)

    # Create export folder and alter the output folder and create it
    # summaryfolder = os.getcwd()+ "/temp/"+part_in.tag+"-bom/"
    summaryfolder = "C:/TinyMRP/temp/"+part_in.tag+"-bom/"
    create_folder_ifnotexists(summaryfolder)

    # Create the SolidBom class object for easier referencing, and override the output folder
    bom_in = solidbom.solidbom_from_flatbom(flatbom, part_in)
    bom_in.folderout = summaryfolder

    # Create the bom
    excelbom = bom_in.solidbom_to_excel()

    path, filename = os.path.split(excelbom)
    if components_only == "YES":
        finalfile = fileserver_path+deliverables_folder+"temp/COMPONENTS_ONLY-"+filename
        #orint("final " ,finalfile)
    else:
        finalfile = fileserver_path+deliverables_folder+"temp/FULL_FLAT_BOM-"+filename
        #orint("final " ,finalfile)

    shutil.copy2(Path(excelbom), Path(finalfile))

    # Remove all the temp files
    os.remove(excelbom)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    # Create the web link
    weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

    return redirect(weblink)


@tinylib.route('/part/label/<partnumber>_rev_<revision>/<processin>_<components_only>', methods=('GET', 'POST'))
@login_required
def process_label_list(partnumber, revision, processin, components_only):

    # Remove spaces from link
    process = processin.replace('%20', ' ')

    rev = ""
    if revision == None or revision == "%" or revision == "" or revision == "%25" or revision == "%2525":
        rev = ""
    else:
        rev = revision

    # Get the top part level object
    part_in = mongoPart.objects(partnumber=partnumber, revision=rev).first()
    # print(part_in)
    # Set qty to one to compute the rest and updatepaths
    part_in.qty = 1
    part_in.updateFileset(fileserver_path, local=True)

    # Add the top part to the list
    flatbom = []
    flatbom.append(part_in)

    # Check if needed to consume the welded components or not
    if components_only == "YES":
        flatbom = flatbom+part_in.get_components(components_only=True)

    else:
        flatbom = flatbom+part_in.get_components(components_only=False)

    # Extract the process related components components
    if part_in.hasProcess(process):
        manbom = []
        manbom.append(part_in)
    elif process == "toplevel":
        manbom = [x for x in part_in.children if not x.hasProcess("hardware")]
    elif process == "all":
        manbom = [x for x in flatbom if not x.hasProcess("hardware")]
        # Sort the list by process
        manbom = sorted(manbom, key=lambda x: x.partnumber, reverse=False)
        manbom = sorted(manbom, key=lambda x: x.process, reverse=False)
    else:
        manbom = [x for x in flatbom if x.hasProcess(process)]

    if len(manbom) == 0 and part_in.hasProcess(process):
        manbom.append(part_in)
    elif len(manbom) == 0:
        return ("NO COMPONENTS WITH THE PROCESS " + process.upper())

    # Create export folder and alter the output folder and create it
    # summaryfolder = os.getcwd() +"/temp/"+part_in.tag+"-"+process.upper() + "_pack/"
    summaryfolder = "C:/TinyMRP/temp/"+part_in.tag+"-"+process.upper() + "_pack/"
    create_folder_ifnotexists(summaryfolder)

    # Create the SolidBom class object for easier referencing, and override the output folder
    bom_in = solidbom.solidbom_from_flatbom(manbom, part_in)
    bom_in.folderout = summaryfolder

    # Assign title
    if process == "toplevel":
        visualtitle = "Top level components"
    else:
        visualtitle = "Visual_summary_components_only-"+components_only + "-"+process

    # Create the visual list
    visuallist = label_list(
        bom_in, outputfolder=summaryfolder, title=visualtitle.replace(" ", "_"))

    # MOVE FILE to temp folder
    path, filename = os.path.split(visuallist)
    finalfile = fileserver_path+deliverables_folder+"temp/"+filename

    shutil.copy2(Path(visuallist), Path(finalfile))

    # Remove all the temp files
    os.remove(visuallist)
    shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

    # Create the web link
    weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

    # print(weblink)

    return redirect(weblink)


# Detail valid inputs: "quick" and "full"
@tinylib.route('/part/pdf/<partnumber>_rev_<revision>', methods=('GET', 'POST'))
@login_required
def pdfwithdescription(partnumber, revision=""):
    commentform = PartComment()
    rev = ""
    if revision == None or revision == "%" or revision == "" or revision == "%25" or \
        revision == "%2525" or revision == "%20%20" or revision==' %25 ':

        rev = ""
    else:
        rev = revision

    if request.method == 'GET':

        part = mongoPart.objects(partnumber=partnumber, revision=rev).first()

        part.updateFileset(webfileserver)
        # MOVE FILE to temp folder
        path, filename = os.path.split(part.pdfpath)
        # remove extension
        filename = os.path.splitext(filename)[0]
        finalfile = fileserver_path+deliverables_folder + \
            "temp/"+filename+"_"+part.description+".pdf"
        finalfile = finalfile.replace(" ", "_")

        print("webfileserver",webfileserver)
        print("fileserver_path",fileserver_path)
        print("filename",filename)
        print("finalfile",finalfile)
        print("""Path(part.pdfpath.replace(webfileserver, fileserver_path))""",
              Path(part.pdfpath.replace(webfileserver, fileserver_path)))
        print("""Path(finalfile)""",
              Path(finalfile))

        try:
            shutil.copy2(Path(part.pdfpath.replace(
                webfileserver, fileserver_path)), Path(finalfile))

            # Create the web link
            weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

            return redirect(weblink)

        except:
            # Create the web link
            weblink = "http://"+part.pdfpath.replace(fileserver_path, webfileserver)

            return redirect(weblink)

    if request.method == 'POST':
        if 'search' in request.form:
            if request.form['search'] != "":

                search = "%" + request.form['search']+"%"
                session['search'] = search

                error = None

                if not search:
                    error = 'A text string required'

                if error is not None:
                    flash(error)
                else:

                    return redirect(url_for('tinylib.search', searchstring=search, page=1))


@tinylib.route('/createjob', methods=['GET', 'POST'])
@permission_required(Permission.WRITE)
def createjob():
    jobs = mongoJob.objects()

    jobform = CreateJob()
    jobcreated = False

    jobform.users.choices = [(str(user.id),user.username) for user in  User.query.all() ]

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()

    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    if request.method == 'POST' and current_user.can(Permission.WRITE) and jobform.validate_on_submit():
        # print("************************************")
        job = mongoJob(jobnumber=jobform.jobnumber.data,  # jobnumber = jobform.jobnumber.data,
                       description=jobform.description.data,
                       customer=jobform.customer.data,

                       user_id=str(current_user._get_current_object().id),
                       # date_due=   jobform.date_due.data,
                       users=jobform.users.data
                       )
        job.save()
        jobcreated = True
        flash("job created successfully")
        flash(job)
        return redirect(url_for('tinylib.createjob', jobs=jobs, form=jobform, searchform=searchform, jobcreated=jobcreated))

    return render_template('tinylib/job_create.html', jobs=jobs, form=jobform, searchform=searchform, jobcreated=jobcreated)


def isjobnumber(jobnumber):
    job = mongoJob.objects(jobnumber=jobnumber).first()
    if job == None:
        return False
    else:

        return True

  
@tinylib.route('/checkjobnumber', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def checkjobnumber():
    # resp=jsonify("Hello World")
    # resp.status_code = 200
    # resp.text="dasfasdf"
    # resp.value="dfasdfa"
    # return resp

    # #print(jsonify(request.args))
    # #print(jsonify(request.args))
    # #print(dir(request))

    jobnumber = request.form['jobnumber']
 
    # if jobnumber:
    # print(jobnumber)

    # print(request.method)
    if jobnumber and request.method == 'POST':
        if isjobnumber(jobnumber):
            # print("existing")
            resp = jsonify(text=1)
            # resp.status_code = 200
            return resp

        else:
            #print("NOT existing")
            resp = jsonify(text=0)
            # resp.status_code = 200
            return resp
    else:
        resp = jsonify(text=-1)
        # resp.status_code = 200
        return resp


@tinylib.route('/jobs', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def jobs_home():

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    # jobs=Job.query.order_by(desc(Job.id))
    jobs = mongoJob.objects().order_by('+jobnumber')

    return render_template('tinylib/jobs.html', jobs=jobs, searchform=searchform)


@tinylib.route('/jobs/manage/<jobnumber>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def job_manage(jobnumber):

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))
    
    job = mongoJob.objects(jobnumber=jobnumber).first()
    jobform = EditJob()

    if request.method == 'GET':
        #print("************ GET ***********")
        
        # Prepopulate with existing data

        

        
        jobform.users.choices = [(str(user.id),user.username) for user in  User.query.all() ]
        jobform.users.data = job.users

        # Debugging: Print or log the values
        print("Choices:", jobform.users.choices)
        print("Current Selections:", jobform.users.data)


        jobform.jobnumber.data = job.jobnumber
        jobform.description.data = job.description
        jobform.customer.data = job.customer
        return render_template('tinylib/job_details.html', job=job, form=jobform, searchform=searchform)
    else:

        jobform.jobnumber.data = job.jobnumber

        # job.jobnumber=jobform.jobnumber.data
        job.description = jobform.description.data
        job.customer = jobform.customer.data
        
        jobform.users.choices = [(str(user.id),user.username) for user in  User.query.all() ]
        job.users=jobform.users.data

        
        job.user_id = str(current_user._get_current_object().id)

        job.save()
        jobcreated = True
        flash("job MODIFIED successfully")
        return render_template('tinylib/job_details.html', job=job, form=jobform, searchform=searchform)


@tinylib.route('/jobs/link/', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def job_link():
    jobnumber = request.values.get('jobnumber')
    job = mongoJob.objects(jobnumber=jobnumber).first()
    joblink = url_for('tinylib.job_manage', jobnumber=jobnumber)
    # print(joblink)

    return joblink


@tinylib.route('/jobs/orderlink/', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def job_orders_link():
    jobnumber = request.values.get('jobnumber')
    ordernumber = request.values.get('ordernumber')
    job = mongoJob.objects(jobnumber=jobnumber).first()
    joblink = url_for('tinylib.job_orders',
                      jobnumber=jobnumber, ordernumber=ordernumber)
    # print(joblink)

    return joblink
 

@tinylib.route('/downloads', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def downloads():

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    return render_template('tinylib/downloads.html', searchform=searchform)


@tinylib.route('/partapi/delete', methods=['GET', 'POST'])
@permission_required(Permission.WRITE)
def deletepart_api():
    partnumber = request.values.get('partnumber')
    revision = request.values.get('revision')
    part = mongoPart.objects(partnumber=partnumber, revision=revision)[0]
    part.delete()
    part.save()
    print("ERASED")

    return jsonify("erased")


@tinylib.route('/partapi/update', methods=['GET', 'POST'])
@permission_required(Permission.WRITE)
def updatepart_api():

    partid = request.values.get('partid')
    partnumber = request.values.get('partnumber')
    revision = request.values.get('revision')
    description = request.values.get('description')
    process = request.values.get('process')
    finish = request.values.get('finish')
    # #print("xxxxxxxxxxxxxxxxxxxx")
    # #print(partid,partnumber,revision,description,process,finish)

    # Findpart
    part = mongoPart.objects(partnumber=partnumber, revision=revision)[0]
    # Update values
    part.description = description
    part.finish = finish

    # Save values
    # part.save()

    return jsonify("updated")


@tinylib.route('/jobapi/delete', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE)
def deletejob():

    request_data = request.values.get('jobnumber')
    # print(request_data)
    request_data = request.values.get('id')
    # print(request_data)
    request_data = request.values.get('description')
    # print(request_data)
    request_data = request.values.get('customer')
    # print(request_data)

    jobnumber = request.values.get('jobnumber')
    jobid = request.values.get('id')

    job = mongoJob.objects(jobnumber=jobnumber).first()
    job.delete()
    # database_job=db.session.query(Job).filter(Job.id==jobid).first()
    # if database_job:
    #     db.session.delete(database_job)
    #     db.session.commit()

    return jsonify(request_data)


@tinylib.route('/jobapi/update', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE)
def updatejob():

    jobid = request.values.get('_id')
    jobnumber = request.values.get('jobnumber')
    jobdescription = request.values.get('description')
    jobcustomer = request.values.get('customer')

    print(jobid, jobnumber, jobdescription, jobcustomer)

    # database_job=db.session.query(Job).filter(Job.id==jobid).first()
    # database_job.id=jobid
    # database_job.jobnumber=jobnumber
    # database_job.description=jobdescription
    # database_job.customer=jobcustomer
    # db.session.commit()

    job = mongoJob.objects(jobnumber=jobnumber).first()
    job.jobnumber = jobnumber
    job.description = jobdescription
    job.customer = jobcustomer
    job.save()

    return jsonify("Success")


@tinylib.route('/jobdata', methods=['GET', 'POST'])
@permission_required(Permission.WRITE)
def data():
    # jobs=Job.query.order_by(desc(Job.id))

    jobs = mongoJob.objects()
    data = []
    # print("dsafad")
    for job in jobs:
        jobdict = job.to_dict()
        # #print(type(jobdict))
        jobdict['id'] = jobdict['_id']
        # jobdict['user']=job.user.username
        # #print(jobdict)
        try:
            jobdict.pop('_sa_instance_state')
        except:
            pass

        data.append(jobdict)

    return mongoToJson({"data": data})


@tinylib.route('/searchdata/<searchstring>', methods=['GET', 'POST'])
def searchdata(searchstring):
    args = json.loads(request.values.get("args"))
    columns = args.get("columns")

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    # print(searchstring)
    search = "%" + searchstring+"%"

    results = Part.query.filter(or_(Part.description.like(search),
                                    Part.partnumber.like(search))).order_by(Part.id.desc())
    data = []
    # print("dsafad")
    for part in results:
        part.updatefilespath(webfileserver)
        part.allprocesses = part.process + " "+part.process2 + " "+part.process3
        partdict = part.__dict__
        partdict.pop('_sa_instance_state')
        data.append(partdict)

    return jsonify({"data": data})


def tree_dict(partin):
    # creates a dictionary with the tree of the part
    reflist = []
    flatbom = []

    partin.updatefilespath(webfileserver)

    partdict0 = partin.as_dict()
    partdict = copy.copy(partdict0)
    partdict['children'] = []
    # orint(partdict)

    def loopchildren(partdict, qty, reflist):
        partnumber = partdict['partnumber']
        revision = partdict['revision']

        part_loop = Part.query.filter_by(
            partnumber=partnumber, revision=revision).first()

        children_loop = part_loop.children_with_qty()

        if len(children_loop) > 0:
            # orint("level",part_loop.partnumber)
            partdict['children'] = []

        for child_loop in children_loop:
            # orint(child_loop)
            child_loop.pngpath = "xxxxx"
            # print(child_loop.pngpath)
            child_loop.updatefilespath(webfileserver)
            # print('object',child_loop.pngpath)
            test = child_loop.pngpath
            # print(test)
            child_dict0 = child_loop.as_dict()
            child_dict = copy.copy(child_dict0)
            child_dict['pngpath'] = test
            #print('dict png path',child_dict['pngpath'])
            child_dict['branch_qty'] = child_loop.qty*qty
            child_dict['qty'] = child_loop.qty

            if len(child_loop.children) > 0:

                # try:
                loopchildren(child_dict, child_dict['branch_qty'], reflist)
                # except:
             #   #print("Problem with", child_loop.partnumber)
              #  #print(traceback.format_exc())

            reflist.append(
                ((child_dict['partnumber'], child_dict['revision']), child_dict['branch_qty']))

            partdict['children'].append(child_dict)

    loopchildren(partdict, 1, reflist)

    # Sum up all quantities and compile flatbom
    resdict = {}
    for item, q in reflist:
        total = resdict.get(item, 0)+q
        resdict[item] = total

    for partrev in resdict.keys():
        flatbom.append(
            {'partnumber': partrev[0], 'revision': partrev[1], 'total_qty': resdict[partrev]})
        # part.qty=resdict[part]
        # flatbom.append(part)

    #flatbom.sort(key=lambda x: (x.category,x.supplier,x.oem,x.approved,x.partnumber))

    # orint(len(flatbom))
    # orint(flatbom)
    partdict['flatbom'] = flatbom

    return partdict


@tinylib.route('/createsupplier', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE)
def createsupplier():
    suppliers = mongoSupplier.objects()

    supplierform = CreateSupplier()
    suppliercreated = False

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()

    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    if request.method == 'POST' and current_user.can(Permission.WRITE) and supplierform.validate_on_submit():
        # print("************************************")
        # print(supplierform.processes.data)

        supplier = mongoSupplier(suppliername=supplierform.suppliername.data,
                                 description=supplierform.description.data,
                                 address=supplierform.address.data,
                                 location=supplierform.location.data,
                                 contact=supplierform.contact.data,
                                 processes=sorted(
                                     list(filter(None, supplierform.processes.data))),

                                 # user_id =str(current_user._get_current_object().id),
                                 # date_due=   supplierform.date_due.data,
                                 )
        # print(supplier)
        supplier.save()
        suppliercreated = True
        flash("supplier created successfully")
        return redirect(url_for('tinylib.createsupplier', suppliers=suppliers, form=supplierform, searchform=searchform, suppliercreated=suppliercreated))

    return render_template('tinylib/supplier_create.html', suppliers=suppliers, form=supplierform, searchform=searchform, suppliercreated=suppliercreated)


def issuppliername(suppliername):
    supplier = mongoJob.objects(suppliername=suppliername).first()
    if supplier == None:
        return False
    else:

        return True


@tinylib.route('/checksuppliername', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def checksuppliername():

    suppliername = request.form['suppliername']

    # print(request.method)
    if suppliername and request.method == 'POST':
        if issuppliername(suppliername):
            # print("existing")
            resp = jsonify(text=1)
            # resp.status_code = 200
            return resp

        else:
            #print("NOT existing")
            resp = jsonify(text=0)
            # resp.status_code = 200
            return resp
    else:
        resp = jsonify(text=-1)
        # resp.status_code = 200
        return resp


@tinylib.route('/createorder', methods=['GET', 'POST'])
@permission_required(Permission.WRITE)
def createorder():
    orders = mongoOrder.objects()

    orderform = CreateOrder()
    ordercreated = False
    # List all the available jobs and force it into the form

    orderform.job.choices = [("", "")]+[(x.jobnumber, x.jobnumber)
                                        for x in mongoJob.objects()]
    # print(orderform.job.choices)

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()

    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    if request.method == 'POST' and current_user.can(Permission.WRITE) and orderform.validate_on_submit():
        # print("************************************")
        order = mongoOrder(ordernumber=orderform.ordernumber.data,  # ordernumber = orderform.ordernumber.data,
                           description=orderform.description.data,
                           job=orderform.job.data,
                           supplier=orderform.supplier.data,
                           user_id=str(current_user._get_current_object().id),
                           # date_due=   orderform.date_due.data,
                           )
        order.save()
        ordercreated = True
        flash("order created successfully")
        return redirect(url_for('tinylib.createorder', orders=orders, form=orderform, searchform=searchform, ordercreated=ordercreated))

    return render_template('tinylib/order_create.html', orders=orders, form=orderform, searchform=searchform, ordercreated=ordercreated)


def isordernumber(ordernumber):
    order = mongoOrder.objects(ordernumber=ordernumber).first()
    if order == None:
        return False
    else:

        return True


@tinylib.route('/checkordernumber', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def checkordernumber():

    ordernumber = request.form['ordernumber']

    # if ordernumber:
    # print(ordernumber)

    # print(request.method)
    if ordernumber and request.method == 'POST':
        if isordernumber(ordernumber):
            # print("existing")
            resp = jsonify(text=1)
            # resp.status_code = 200
            return resp

        else:
            #print("NOT existing")
            resp = jsonify(text=0)
            # resp.status_code = 200
            return resp
    else:
        resp = jsonify(text=-1)
        # resp.status_code = 200
        return resp


@tinylib.route('/jobapi/addtobom', methods=['GET', 'POST'])
@permission_required(Permission.WRITE)
def addtojobbom():

    # print("*********************************")
    # print("*********************************")
    # print("*********************************")
    # print("*********************************")

    jobnumber = request.values.get('jobnumber')
    partnumber = request.values.get('partnumber')
    revision = request.values.get('revision')

    print(jobnumber, partnumber, revision)
    # print("*********************************")

    part = mongoPart.objects(partnumber=partnumber, revision=revision).first()
    job = mongoJob.objects(jobnumber=jobnumber).first()

    bom = mongoBom(part=part, qty=1)

    present = False
    for bombit in job.bom:
        if part.id == bombit.part.id:
            present = True
            bombit.qty = bombit.qty+1
            job.save()
            return jsonify("Success")

    if not present and part != None and job != None:
        job.bom.append(bom)
        job.save()
        return jsonify("Success")


@tinylib.route('/jobapi/removefrombom', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def removefrombom():

    # print("*********************************")
    # print("*********************************")
    # print("*********************************")
    # print("*********************************")

    jobnumber = request.values.get('jobnumber')
    partnumber = request.values.get('partnumber')
    revision = request.values.get('revision')

    print(jobnumber, partnumber, revision)
    # print("*********************************")

    part = mongoPart.objects(partnumber=partnumber, revision=revision).first()
    job = mongoJob.objects(jobnumber=jobnumber).first()

    bom = mongoBom(part=part, qty=1)

    present = False
    for bombit in job.bom:
        if part.id == bombit.part.id:
            present = True
            bombit.qty = bombit.qty-1

            if bombit.qty < 1:
                job.bom.remove(bombit)

            job.save()
            return jsonify("Success")

    if not present and part != None and job != None:
        job.bom.append(bom)
        job.save()
        return jsonify("Success")


@tinylib.route('/jobs/manageorders/<jobnumber>/<ordernumber>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def job_orders(jobnumber, ordernumber):

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    if request.method == 'GET':
        #print("************ GET ***********")
        job = mongoJob.objects(jobnumber=jobnumber).first()
        # Prepopulate with existing data
        orders = mongoOrder.objects(job=jobnumber)
        print(orders)
        order = mongoOrder.objects(ordernumber=ordernumber).first()
        print(order)

        if order == None or order == 'all':
            return render_template('tinylib/job_orders.html', job=job, ordernumber=ordernumber,  orders=orders, searchform=searchform)
        else:
            orderbom = []
            for bomline in order.bom:
                outdict = bomline.part.to_dict()
                outdict['qty'] = bomline.qty

                print(outdict['pngpath'])

                if outdict['partnumber'] != None:
                    if outdict['revision'] == "":
                        urllink = url_for(
                            'tinylib.partnumber', partnumber=outdict['partnumber'], revision="%25")
                        # #print(urllink)
                    else:
                        # print(part.partnumber)
                        urllink = url_for(
                            'tinylib.partnumber', partnumber=outdict['partnumber'], revision=outdict['revision'])
                        # #print("the part link" , urllink)

                    # try:
                    #     outdict['pngpath']= '<a href="'+ urllink +  '">' + """<img src='""" + "http://"+outdict['pngpath'] + """' width=auto height=30rm></a>"""
                    #     # #print("the image link" , part['pngpath'])
                    # except:
                    #     pass
                orderbom.append(outdict)
            return render_template('tinylib/job_orders.html', job=job, ordernumber=ordernumber,  orders=orders, orderbom=orderbom, searchform=searchform)


@tinylib.route('/jobapi/addtoorder', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def addtoorder():

    # print("*********************************")
    # print("*********************************")
    # print("*********************************")
    # print("*********************************")

    print(request.args)
    jobnumber = request.values.get('jobnumber')
    ordernumber = request.values.get('ordernumber')
    alldata = request.values.get('alldata')

    order = mongoOrder.objects(ordernumber=ordernumber).first()
    print("ORDER TO BE ADDED THE PART")
    print(order)
    print(order.to_dict())
    print(order.bom)

    alldata = json.loads(alldata)
    print(alldata)
    for indict in alldata:
        print(indict)
        print(indict['partnumber'], indict['qty'],
              indict['branchqty'], indict['totalqty'])
        partin = mongoPart.objects(
            partnumber=indict['partnumber'], revision=indict['revision']).first()
        present = False
        complete = False
        for bomline in order.bom:
            if partin.id == bomline.part.id:
                present = True
                bomline.qty = int(bomline.qty)+int(indict['branchqty'])
                order.save()
                # if indict['totalqty']>bomline.qty:
                #     bomline.qty=bomline.qty+indict['branchqty']
                #     order.save()
            # else:
            #     flash(partin.partnumber," already in current order")
        if not present:
            try:
                bomin = mongoBom(part=partin, qty=int(indict['branchqty']))
            except:
                bomin = mongoBom(part=partin, qty=int(indict['totalqty']))
            order.bom.append(bomin)
            print(bomin)
            order.save()

    # print(jobnumber)
    # print(ordernumber)
    # print(alldata)
 
    # print (jobnumber, partnumber,revision)
    # #print("*********************************")

    # part=mongoPart.objects(partnumber=partnumber,revision=revision).first()
    # job=mongoJob.objects(jobnumber=jobnumber).first()

    # bom=mongoBom(part=part,qty=1)

    # present=False
    # for bombit in job.bom:
    #     if part.id==bombit.part.id:
    #         present=True
    #         bombit.qty=bombit.qty+1
    #         job.save()
    #         return jsonify("Success")
 
    # if not present and part!=None and job!=None:
    #     job.bom.append(bom)
    #     job.save()
    return jsonify("Success")



@tinylib.route('/api/docpack', methods=['GET', 'POST'])
@login_required
def compile_pack():
    compileform=Compile()

    if request.method == 'POST':

        #Store form data into dictionary and retype the non list values
        form_dict=dict(request.form.lists())
        #print(form_dict)
        for key in form_dict.keys():
            if type(form_dict[key])==list: 
                if len(form_dict[key])==1: form_dict[key]=form_dict[key][0]       

        if 'watermark_opt' in form_dict.keys():
            watermark=form_dict['watermark_opt']

            if watermark==None or isinstance(watermark,str):
                watermark=[watermark]
        else:
            watermark=[]

        #Get root mongopart instance
        part= mongoPart.objects(
            partnumber=form_dict['partnumber'], revision=form_dict['revision']).first()


        # Tree data creation including the consumed and depth of bom 
        # and add root part
        if part!=None:
            temptreedata=json.loads(mongotreepartdata(partnumber=part.partnumber,
                                                        revision=part.revision,
                                                        web=False,
                                                        depth=form_dict['bom_opt'],
                                                        structure='flat',
                                                        consume=form_dict['consumed_opt']
                                                        ))['data']

            rootdict=part.to_dict()
            rootdict['qty']=1; rootdict['totalqty']=1;rootdict['branchqty']=1; rootdict['level']="+"
            temptreedata=[rootdict]+temptreedata            


        #level normalization for sorting
        for parto in temptreedata:
            parto['level']=str(" ".join(parto['level']))            
                       

        #Classified filtering
        classified=form_dict['classified_opt']
        if classified=='hide':
            temptreedata=[obj for obj in temptreedata if obj['classified'] != 'yes']
        elif classified=='only':
            temptreedata=[obj for obj in temptreedata if obj['classified'] == 'yes']

   
        if form_dict['filterprocess_opt']=='yes':
            treedata=[]
            for parto in temptreedata:
                                        keep=False                                        
                                        
                                        for process in parto['process']:
                                            if 'processes' in form_dict.keys():
                              
                                                    if process in form_dict['processes'] or process == form_dict['processes']: keep=True
                              
                                            if process not in config['PROCESS_CONF'].keys() and 'others' in form_dict['processes']: keep=True
                                        if keep:
                                            treedata.append(parto)
                                            
        else:
            treedata=temptreedata


        #Final dict list of parts        
        print(form_dict)

     
        #Temporary folder
        outputfolder="C:/TinyMRP/temp/"+"docpack" + \
                    datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+"/"
        
        create_folder_ifnotexists(outputfolder)



        if 'export_opt' in form_dict.keys():
            title=part.partnumber+" REV "+part.revision + ":"  
            subtitle= "Consumed parts: " +form_dict['consumed_opt']+ " - Classified: " + form_dict['classified_opt'] + " - Depth: " + form_dict['bom_opt'] +   \
                        " - Processes: " 
            subtitle=part.description
            
                        
            # if 'processes' in form_dict.keys():
            #     if type (form_dict['processes'])== list:
            #         subtitle=subtitle+ ", ".join(form_dict['processes'])
            #     else:
            #         subtitle=subtitle+ form_dict['processes']
                
            if 'fabpack' in form_dict['export_opt']:  

                fabbom,faball=fabdict(part,show_classified=form_dict['classified_opt'])
                fabbom.sort(key=lambda item: item.get("partnumber"),reverse=True)
                fabbom.sort(key=lambda item: item.get("process"), reverse=True)
                faball.sort(key=lambda item: item.get("partnumber"))

                visualpack=visual_list(fabbom,outputfolder=outputfolder,title="FABRICATION_SCOPEOFSUPPLY_"+title,subtitle=subtitle,local=True,scopeofsupply=True)
                BinderPDF(faball,outputfolder=outputfolder,title="FABRICATION_DRAWINGPACK_"+title,subtitle=subtitle,savevisual=False)
            

            if 'visual' in form_dict['export_opt']:
                visualpack=visual_list(treedata,outputfolder=outputfolder,title=title,subtitle=subtitle,local=True)

            if 'files' in form_dict['export_opt']:
                if 'files' in form_dict.keys():
                    zipfileset(treedata, form_dict['files'],outputfolder=outputfolder, delTempFiles=False)
                else:
                    flash ('Select filetypes for individual files pack','error')
                    return redirect(url_for('tinylib.partnumber',partnumber=part['partnumber'],revision=part['revision']))

            if 'binder' in form_dict['export_opt']:
                treedata.sort(key=lambda item: item.get("partnumber"))
                BinderPDF(treedata,outputfolder=outputfolder,title=title,subtitle=subtitle,savevisual=False, stamps=watermark)

            if 'excel' in form_dict['export_opt']:
                treedata.sort(key=lambda item: item.get("partnumber"))
                excel_list = dictlist_to_excel(treedata, outputfolder,
                                 title=part.partnumber+" REV "+part.revision+"_"+datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f'))

       

        weblink, filepath=zipfolderforweb(outputfolder, filepath_feedback=True)
        if 'processes' in form_dict.keys():
            print(form_dict['processes'])

        #Delete compiled files after 30 seconds if not downloaded
        threading.Thread(target=delayed_remove, args=(filepath, 30)).start()
              
        return render_template('tinylib/excelcompile.html', upload=True, weblink=weblink, filepath=os.path.basename(filepath))
    


def fabdict(partin, qty=1,level="+1",show_classified="show"):

        reflist=[]
        flatbom=[]
        scope=[]
        packinglist=[]

        def loopchildrenfab(part,qty,reflist,scope,packinglist,level="",infab=False):

                    
            i=0
            for line in part.bom:
                i+=1
                print(line.part)

                branchqty=line['qty']*qty
                bomqty=line['qty']
                if i<10:
                    reflevel=level+".0"+str(i)
                else:
                    reflevel=level+"."+str(i)
                reflist.append([line['part'],branchqty,bomqty,reflevel])

                if infab:
                    if line['part'].hasProcess('welding') or line['part'].hasProcess('lasercut') or line['part'].hasProcess('cutting') or line['part'].hasProcess('folding') :
                        scope.append(line.part['partnumber'])
                else:
                    if line['part'].hasProcess('welding') or line['part'].hasProcess('lasercut') or line['part'].hasProcess('cutting') or line['part'].hasProcess('folding') :
                        scope.append(line.part['partnumber'])
                        packinglist.append(line.part['partnumber'])
                

                if  len(line['part']['bom'])>0:
                    # reflist.append((child['part'],branchqty))                    

                    if line['part'].hasProcess('welding') :
                        loopchildrenfab(line['part'],branchqty,reflist,scope,packinglist,level=reflevel,infab=True)
                    else:
                        loopchildrenfab(line['part'],branchqty,reflist,scope,packinglist,level=reflevel,infab=False)
                # else:
                #     reflist.append((child['part'],branchqty))
                    
        loopchildrenfab(partin,qty,reflist,scope,packinglist,level=level,infab=False)


    


        #Sum up all quantities and compile flatbom
        totalsdict={}
        bomlist=[]

        for part,branchqty,bomqty,level in reflist:
            total=totalsdict.get(part,0)+branchqty
            totalsdict[part]=total
            #part.getweblinks()
            
            partdict=part.to_dict()
            partdict['qty']=bomqty
            partdict['branchqty']=branchqty
            partdict['level']=level
            
            if part['partnumber'] in scope: 
                # if not show_classified:
                #     if 'classified' in partdict:
                #         if partdict['classified'].lower()=='yes' :
                #             print("NOT NOT NOT NOT ADDED")
                #             print(partdict['partnumber'],partdict['classified'])
                #             print("NOT NOT NOT NOT ADDED")
                            
                            
                #         else:
                #             bomlist.append(partdict)
                #             print("YES YES YES YES ADDED")
                #             print(partdict['partnumber'],partdict['classified'])
                #             print("YES YES YES YES ADDED")
                #     else:
                #         bomlist.append(partdict)

                # else:
                #     bomlist.append(partdict)
                bomlist.append(partdict)
            
        #Store the total quantities for the flatbom
        for part in totalsdict.keys():
            part['totalqty']=totalsdict[part]
            part['level']=[]
            part['qty']=[]
            part['branchqty']=[]
            # print(part,part['totalqty'])
            
            for partdict in bomlist:
                if partdict['partnumber']==part.partnumber and partdict['revision']==part.revision:
                    partdict['totalqty']=part['totalqty']
                    part['level'].append(partdict['level'])
                    part['qty'].append(partdict['qty'])
                    part['branchqty'].append(partdict['branchqty'])
            if part['partnumber'] in scope:           
                flatbom.append(part)


        flatdictlist=[]
        for part in flatbom:
            # if show_classified=='only':
            #     if part['classified'].lower()=='yes':
            #         flatdictlist.append(part.to_dict())
            # else:
                flatdictlist.append(part.to_dict())
        flatbom=flatdictlist

        scope_dictlist=[]
        for partbom in bomlist:
            if partbom['partnumber'] in packinglist:
                repeated=False
                for part in scope_dictlist:
                    if partbom['partnumber']==part['partnumber']:
                        repeated=True
                if not repeated:
                    # if show_classified=='only':
                    #     if partbom['classified'].lower()=='yes':
                    #         scope_dictlist.append(partbom)
                    
                    # else:
                        scope_dictlist.append(partbom)
        
        # print("bomlist@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("bomlist@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print(bomlist)
        # print("bomlist@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("bomlist@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("packinglist@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("packinglist@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print(packinglist)
        # print("packinglist@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("packinglist@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("SCOPE@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("SCOPE@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print(scope)
        # print("SCOPE@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print("SCOPE@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # print(flatbom)

        if show_classified=='hide':
            scope_dictlist=[obj for obj in scope_dictlist if obj['classified'] != 'yes']
            flatbom=[obj for obj in flatbom if obj['classified'] != 'yes']

        elif show_classified=='only':
            scope_dictlist=[obj for obj in scope_dictlist if obj['classified'] == 'yes']
            # flatbom=[obj for obj in flatbom if obj['classified'] == 'yes']
        
        return scope_dictlist,flatbom





def delayed_remove(path, delay):
    """
    Wait for the specified delay and then remove the file.
    """
    time.sleep(delay)
    maxtries=50
    tries=0
    while tries<maxtries:
        try:
            os.remove(path)
            print(f"Successfully removed {path}")
            tries=maxtries
        except Exception as e:
            print(f"Error removing {path}: {e}")
            tries=tries+1



# To serve files and deletethem after the download 
@tinylib.route('/downloadfile/<filename>', methods=['GET', 'POST'])
@login_required
def downloadfile(filename):
    
    folder=fileserver_path+deliverables_folder+"temp/"
    file_path = os.path.join(folder, filename)

    print(file_path)

    # Ensure the file exists
    if not os.path.exists(file_path):
        return "File not found.", 404

    # Function to remove the file after sending it
    @after_this_request
    def remove_file(response):
        try:
            delay = 30 # seconds
            threading.Thread(target=delayed_remove, args=(file_path, delay)).start()
            # os.remove(file_path)
            # flash(f"Succe+ssfully removed {file_path}")
            print(f"Succe+ssfully removed {file_path}")
        except Exception as error:
            # flash(f"Error removing {file_path}: {error}")
            print(f"Error removing {file_path}: {error}")

        return response

    # Send the file and then delete it
    return send_file(file_path, as_attachment=True)



@tinylib.route('/cleandatabase', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADMIN)
def cleandatabase():
    print("eeoeo")
    mongoPart.objects.delete()
    return jsonify(message="All documents deleted successfully.")



@tinylib.route('/load3d', methods=['GET', 'POST'])
def load_3d():

    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and file.filename.endswith('.3mf'):
            filename = file.filename
            targetfolder=fileserver_path+deliverables_folder+"temp/"+ "/" + config['UPLOAD_PATH'] + "/"
            print(os.path.join(targetfolder, filename))
            file.save(os.path.join(targetfolder, filename))
            return 'File uploaded successfully'
    elif request.method == 'GET':
        return render_template('loader3d.html')
