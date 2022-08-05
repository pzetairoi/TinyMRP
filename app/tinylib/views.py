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
    jsonify
)
from cmath import nan
from flask import jsonify
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

def zipfolderforweb(summaryfolder, delTempFiles=True):
        zipfile = Path(shutil.make_archive(Path(summaryfolder), 'zip', Path(summaryfolder)))
        #print("original " ,zipfile)

        path, filename = os.path.split(zipfile)
        finalfile = fileserver_path+deliverables_folder+"temp/"+filename
        #print("final " ,finalfile)

        shutil.copy2(Path(zipfile), Path(finalfile))

        # Remove all the temp files
        os.remove(zipfile)
        if delTempFiles:
            shutil.rmtree(Path(summaryfolder), ignore_errors=False, onerror=None)

        # Create the web link
        weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

        print(weblink)

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
        summaryfolder = os.getcwd()+"/temp/"+"datatablecompile" + \
                    datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+"/"
    create_folder_ifnotexists(summaryfolder)

    fileset = []
    for filetype in config['FILES_CONF'].keys():
        if config['FILES_CONF'][filetype]['list'] == 'yes':
            refdict = config['FILES_CONF'][filetype]
            refdict['filetype'] = filetype
            
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

                    filepairs.append(
                        [filetype['filetype'], filetype['folder'], filetype[extension], filetype['filemod'],filetype['finalfolder']])

    # print("filepairssssss", filepairs)

    # Loop over the fabrication components and create files
    for index, part in enumerate(partlist):
        filenamebit = part["partnumber"]+"_REV_"+part["revision"]

        for filetype, folder, extension, filemod,finalfolder in filepairs:
            sourcefile = fileserver_path+deliverables_folder + \
                folder+"/"+filenamebit+filemod+"."+extension
            # print(sourcefile)
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
                    print("TARGETFILEERRROR",part)
                    pass

            if os.path.exists(sourcefile.replace(webfileserver, fileserver_path)):
                copyfile(sourcefile.replace(
                    webfileserver, fileserver_path), targetfile)
                # print(sourcefile,targetfile)
            else:
                print("NOFILE - ", sourcefile)
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
    print("cocucocuoucoucouco", count)

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
def mongotreepartdata(partnumber="",revision="",depth='toplevel',web=True,consume='hide',structure='flat'):

    # print("***",request.values)

    # Part tree filter
    try:
        rootnumber = request.values.get('rootnumber')
        rootrevision = request.values.get('rootrevision')
        jobnumber = request.values.get('jobnumber')
        ordernumber = request.values.get('ordernumber')
        structured = request.values.get('structure')
        consumed = request.values.get('consume')
        level = request.values.get('level')
        processlist = json.loads(request.values.get('processlist'))
        
        
    except:
        rootnumber =""
        rootrevision  =""
        jobnumber  =""
        ordernumber  =""
        structured  =""
        consumed  =""
        level  =""
        processlist =[]
        


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


    #Options from the api on the export
    if level == 'yes' or depth=='full':
        fulltree = True
    else:
        fulltree = False
    
    if consumed == 'yes' or consume=='show':
        consume = True
    else:
        consume = False
        
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


    # Get all the ordered parts:
    joborders = mongoOrder.objects(job=jobnumber).all()
    totalorder = []
    totalsdict = {}
    
    for order in joborders:
        # print(order)
        for bomline in order.bom:
            total = totalsdict.get(bomline.part, 0)+bomline.qty
            totalsdict[bomline.part] = total

    orderedlist = []
    
    for part in totalsdict.keys():
        orderedlist.append({'partnumber': part.partnumber,
                        'revision': part.revision, 'orderedqty': totalsdict[part]})

    # Get all teh components in a dictionary format
    dictlist = root.get_components(
                bomdictlist=True, level="+", structure=structure, consume=consume, fulltree=fulltree)



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

    search = request.args.get('columns[12][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower()
                        in x['supplier'].lower()]

    search = request.args.get('columns[13][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            dictlist = [x for x in dictlist if chunk.lower(
            ) in x['supplier_partnumber'].lower()]

    search = request.args.get('columns[14][search][value]')
    if search:
        splitsearch = search.lstrip().rstrip().split(" ")
        cleansearch = [float(x) for x in splitsearch]
        # print(cleansearch)
        dictlist = [x for x in dictlist if x['thickness'] in cleansearch]

    search = request.args.get('columns[15][search][value]')
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
                part['pngpath'] = '<a href="' + urllink + '">' + """<img src='""" + \
                    "http://"+ part['pngpath'].replace(fileserver_path,webfileserver) +  """' width=auto height=30rm></a>"""
        elif part['partnumber'] != None:
            pass

        else:
            part['pngpath']=webfileserver+'/logo.png'
                
                

            # Putting icons instead of text
            # iconhtml="<div>"
            # for i,icon in enumerate(part['process_icons']):
            #          iconhtml=iconhtml+  """<img src='""" + url_for('static', filename=icon) + """'  hspace=5 vspace=5  margin=0 height=auto width=25rm  >"""
            # part['process']=iconhtml+"</div>"
        
        #Account for the ordered parts for ORDERS
        # for part in dictlist:
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

    #query = Part.query

    # Global search filter
    search = request.args.get('search[value]')

    # Job only filter
    jobnumber = request.values.get('jobnumber')
    ordernumber = request.values.get('ordernumber')
    # print(ordernumber)

    # Part tree filter
    rootnumber = request.values.get('rootnumber')
    rootrevision = request.values.get('rootrevision')

    job = mongoJob.objects(jobnumber=jobnumber).first()
    order = mongoOrder.objects(ordernumber=ordernumber).first()
    root = mongoPart.objects(partnumber=rootnumber,
                             revision=rootrevision).first()

    if job != None:
        allparts = mongoPart.objects(id__in=job.flatbomid())
        if order != None:
            allparts = allparts(id__in=order.flatbomid())
    elif order != None:
        allparts = mongoPart.objects(id__in=order.flatbomid())
    elif root != None:
        allparts = mongoPart.objects(id__in=root.flatbomid())
    else:
        allparts = mongoPart.objects()

    # Total records for the children
    recordsTotal = allparts.count()

    if search == "" or not search:
        pass
    else:
        allparts = allparts(Q(description__icontains=search)
                            | Q(partnumber__icontains=search))

    # # SearchPanes
    searchpanes = {}
    # searchpanes = {'options':{}}
    # sp_fields=['process','finish']
    # for sp_field in sp_fields:
    #     # init SearchPanes
    #     # names = [row[0] for row in db.session.query(getattr(Expert, sp_field).distinct()).all()]
    #     names=allparts.distinct(field=sp_field)

    #     searchpanes['options'][sp_field]=[]
    #     for name in names:
    #         panequery={sp_field:name}

    #         name_d = {"label": name,
    #         #    "total": query.filter(getattr(Expert, sp_field)==name).count(),
    #            "total": len(allparts(__raw__=panequery)),
    #            "value": name,
    #         #    "count": query.filter(getattr(Expert, sp_field)==name).count()}
    #            "count": len(allparts(__raw__=panequery))}
    #         searchpanes['options'][sp_field].append(name_d)
    #         # print("$$$$$$$$",allparts(sp_field=name).count())
    #     # SearchPanes filter

    #     requeststring="searchPanes["+sp_field+"][0]"
    #     # print(sp_field,request.values.get(requeststring))
    #     # print(request.values)

    #     if request.values.get(requeststring):
    #         # print("$$$$$$$$")
    #         sp_filter = []
    #         i = 0
    #         while True:
    #             requestCOLstring="searchPanes["+sp_field+"]["+str(i)+"]"
    #             col_name = request.values.get(requestCOLstring)

    #             if col_name is None:
    #                 break
    #             sp_filter.append(col_name)
    #             i += 1
    #         # print(sp_filter)
    #         # print("$$$$$$$$",len(allparts))
    #         filterquery={sp_field:{"$in":sp_filter}}
    #         allparts=allparts(__raw__=filterquery)
    #         # print("$$$$$$$$",len(allparts))
    #         # query = query.filter(getattr(Expert, sp_field).in_(sp_filter))

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
            allparts = allparts(supplier__icontains=chunk)

    search = request.args.get('columns[9][search][value]')
    if search:
        splitsearch = search.split(" ")
        for chunk in splitsearch:
            allparts = allparts(supplier_partnumber__icontains=chunk)

    search = request.args.get('columns[10][search][value]')
    if search:
        splitsearch = search.lstrip().rstrip().split(" ")
        cleansearch = [float(x) for x in splitsearch]
        # print(cleansearch)
        allparts = allparts(thickness__in=cleansearch)

    search = request.args.get('columns[11][search][value]')
    if search:
        splitsearch = search.lstrip().rstrip().split(" ")
        splitsearch = [float(x) for x in splitsearch]
        maxval = max(splitsearch)
        minval = min(splitsearch)

        if maxval != minval:
            allparts = allparts(mass__gte=minval)
            allparts = allparts(mass__lte=maxval)
        else:
            allparts = allparts(mass__gte=minval)

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

    # Modify the imagelink
    webdata = []
    for part in paginatedparts:
        part.updateFileset(web=True)

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
    # #print(jsonify(tabledata))
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
        targetfolder = os.path.dirname(os.path.abspath(
            __file__)) + "/" + config['UPLOAD_PATH'] + "/"
        targetfile = targetfolder + f
        filestring = Path(targetfile).stem

        # Save uploaded file
        bomform.file.data.save(targetfile)

        # unzip file
        shutil.unpack_archive(targetfile, targetfolder, "zip")

        bomfolder = targetfolder+"/"+filestring
        bomfile = bomfolder+"/"+filestring+"_TREEBOM.txt"
        flatfile = bomfolder+"/"+filestring+"_FLATBOM.txt"

        # Remove original file
        try:
            os.remove(targetfile)
        except:
            flash("Couldn't erase upload file ", targetfile)

        # Create the SOLIDBOM
        bom_in = solidbom(bomfile, flatfile,
                          deliverables_folder, fileserver_path+folderout)

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
@permission_required(Permission.MODERATE)
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
        summaryfolder = os.getcwd()+"/temp/"+"excelcompile" + \
            datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+"/"
        create_folder_ifnotexists(summaryfolder) 


        pdf_pack = BinderPDF( part_dict_list, outputfolder=summaryfolder,savevisual=True)

        # Copy original excel file to export folder
        shutil.copy2(Path(targetfile), Path(summaryfolder+"inputfile" +
                     datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+".xlsx"))

        # Get all files of the flatbom
        
        zipfileset(part_dict_list, ['pdf', 'dxf', 'step'],outputfolder=summaryfolder, delTempFiles=False)

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

        # Clean original file
        try:

            os.remove(targetfile)
        except:
            #print("Couldn't erase upload file ", targetfile)
            flash("Couldn't erase upload file ", targetfile)

        return render_template('tinylib/excelcompile.html', excelform=excelform, upload=True, weblink=weblink, searchform=searchform)

    else:
        return render_template('tinylib/excelcompile.html', excelform=excelform, upload=False, weblink=False, searchform=searchform)


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


    summaryfolder = os.getcwd()+"/temp/"+part.get_tag()+"/"
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
    summaryfolder = os.getcwd()+"/temp/"+part_in.tag+"-fabrication_pack/"
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
    summaryfolder = os.getcwd()+"/temp/"+part_in.tag+"-"+process.upper() + \
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
    summaryfolder = os.getcwd()+"/temp/"+part_in.tag+"-"+process.upper() + "_pack/"
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
    summaryfolder = os.getcwd()+"/temp/"+part_in.tag+"-bom/"
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
    summaryfolder = os.getcwd()+"/temp/"+part_in.tag+"-"+process.upper() + "_pack/"
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

        shutil.copy2(Path(part.pdfpath.replace(
            webfileserver, fileserver_path)), Path(finalfile))

        # Create the web link
        weblink = "http://"+finalfile.replace(fileserver_path, webfileserver)

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
def createjob():
    jobs = mongoJob.objects()

    jobform = CreateJob()
    jobcreated = False

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
                       )
        job.save()
        jobcreated = True
        flash("job created successfully")
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
@permission_required(Permission.MODERATE)
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
def job_manage(jobnumber):

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    jobform = EditJob()

    if request.method == 'GET':
        #print("************ GET ***********")
        job = mongoJob.objects(jobnumber=jobnumber).first()
        # Prepopulate with existing data

        jobform.jobnumber.data = job.jobnumber
        jobform.description.data = job.description
        jobform.customer.data = job.customer
        return render_template('tinylib/job_details.html', job=job, form=jobform, searchform=searchform)
    else:

        # if  request.method == 'POST' and current_user.can(Permission.WRITE) and jobform.validate_on_submit():
        #print("************** POST ********************")
        job = mongoJob.objects(jobnumber=jobnumber).first()

        jobform.jobnumber.data = job.jobnumber

        # job.jobnumber=jobform.jobnumber.data
        job.description = jobform.description.data
        job.customer = jobform.customer.data
        job.user_id = str(current_user._get_current_object().id)

        job.save()
        jobcreated = True
        flash("job MODIFIED successfully")
        return render_template('tinylib/job_details.html', job=job, form=jobform, searchform=searchform)


@tinylib.route('/jobs/link/', methods=['GET', 'POST'])
@login_required
def job_link():
    jobnumber = request.values.get('jobnumber')
    job = mongoJob.objects(jobnumber=jobnumber).first()
    joblink = url_for('tinylib.job_manage', jobnumber=jobnumber)
    # print(joblink)

    return joblink


@tinylib.route('/jobs/orderlink/', methods=['GET', 'POST'])
@login_required
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
@permission_required(Permission.MODERATE)
def downloads():

    # Simple search snippet to add to every view   methods=['GET', 'POST'])
    searchform = SearchSimple()
    if searchform.validate_on_submit():
        searchstring = searchform.search.data
        session['search'] = searchstring
        return redirect(url_for('tinylib.search', searchstring=searchstring, page=1, searchform=searchform))

    return render_template('tinylib/downloads.html', searchform=searchform)


@tinylib.route('/partapi/delete', methods=['GET', 'POST'])
def deletepart_api():
    partnumber = request.values.get('partnumber')
    revision = request.values.get('revision')
    part = mongoPart.objects(partnumber=partnumber, revision=revision)[0]
    part.delete()
    part.save()
    print("ERASED")

    return jsonify("erased")


@tinylib.route('/partapi/update', methods=['GET', 'POST'])
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
@permission_required(Permission.MODERATE)
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
@permission_required(Permission.MODERATE)
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

    alldata = json.loads(alldata)
    for indict in alldata:
        # print(indict)
        print(indict['partnumber'], indict['qty'],
              indict['branchqty'], indict['totalqty'])
        partin = mongoPart.objects(
            partnumber=indict['partnumber'], revision=indict['revision']).first()
        present = False
        complete = False
        for bomline in order.bom:
            if partin.id == bomline.part.id:
                present = True
                bomline.qty = bomline.qty+indict['branchqty']
                order.save()
                # if indict['totalqty']>bomline.qty:
                #     bomline.qty=bomline.qty+indict['branchqty']
                #     order.save()
            # else:
            #     flash(partin.partnumber," already in current order")
        if not present:
            bomin = mongoBom(part=partin, qty=indict['branchqty'])
            order.bom.append(bomin)
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
        for key in form_dict.keys():
            if type(form_dict[key])==list: 
                if len(form_dict[key])==1: form_dict[key]=form_dict[key][0]

       
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
                                                        consume=form_dict['consumed_opt']))['data']

            rootdict=part.to_dict()
            rootdict['qty']=1; rootdict['totalqty']=1;rootdict['branchqty']=1; rootdict['level']="+"
            temptreedata=[rootdict]+temptreedata            
            print("cuantas before process filter",len(temptreedata))
            

        #Final dict list of parts
        treedata=[]

       #Process filter and level normalization for sorting
        for parto in temptreedata:
            parto['level']=str(" ".join(parto['level']))           
            keep=False
            print(parto['partnumber'],parto['pngpath'])    
            for process in parto['process']:
                if process in form_dict['processes']: keep=True
                if process not in config['PROCESS_CONF'].keys() and 'others' in form_dict['processes']: keep=True
            if keep:
                treedata.append(parto)

        for dicto in treedata:
            print(dicto['pngpath'])

                        


        #Sort the treedata with the level
        treedata.sort(key=lambda item: item.get("process"))
        

        #Temporary folder
        outputfolder=os.getcwd()+"/temp/"+"docpack" + \
                    datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f')+"/"
        
        create_folder_ifnotexists(outputfolder)

               
         

        if 'export_opt' in form_dict.keys():
            title=part.partnumber+" REV "+part.revision + ":"  
            subtitle= "Consumed parts: " +form_dict['consumed_opt']+ " - Depth: " + form_dict['bom_opt'] +   \
                        " - Processes: " 
            if type (form_dict['processes'])== list:
                subtitle=subtitle+ ", ".join(form_dict['processes'])
            else:
                subtitle=subtitle+ form_dict['processes']
            

            if 'visual' in form_dict['export_opt']:
                visualpack=visual_list(treedata,outputfolder=outputfolder,title=title,subtitle=subtitle,local=True)

            if 'files' in form_dict['export_opt']:
                if 'files' in form_dict.keys():
                    zipfileset(treedata, form_dict['files'],outputfolder=outputfolder, delTempFiles=False)
                else:
                    flash ('Select filetypes for individual files pack','error')
                    return redirect(url_for('tinylib.partnumber',partnumber=part['partnumber'],revision=part['revision']))

            if 'binder' in form_dict['export_opt']:
                BinderPDF(treedata,outputfolder=outputfolder,title=title,subtitle=subtitle,savevisual=False)

            if 'excel' in form_dict['export_opt']:
                excel_list = dictlist_to_excel(treedata, outputfolder,
                                 title=part.partnumber+" REV "+part.revision+"_"+datetime.now().strftime('%d_%m_%Y-%H_%M_%S_%f'))

       

        weblink=zipfolderforweb(outputfolder)
        print(form_dict['processes'])
              
        return redirect(weblink)
