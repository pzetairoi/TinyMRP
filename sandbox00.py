
from re import RegexFlag


RegexFlag
child\.(\w*)
child['$1']


        def loopchildren(part,qty,reflist,level=""):

                    
            i=0
            for line in part.bom:
                i+=1
                # print(line.part)

                branchqty=line['qty']*qty
                bomqty=line['qty']
                if i<10:
                    reflevel=level+".0"+str(i)
                else:
                    reflevel=level+"."+str(i)
                
                reflist.append([line['part'],branchqty,bomqty,reflevel])
                if  len(line['part']['bom'])>0 and (not consume) and (not line['part'].hasConsumingProcess()):
                      loopchildren(line['part'],branchqty,reflist,level=reflevel)
                # else:
                #     reflist.append((child['part'],branchqty))
        # if  len(self['bom'])>0 and (not consume) and ( not self.hasConsumingProcess()):
        loopchildren(self,qty,reflist,level=level)


{ datasheet: { $exists: true, $ne:"",$regex:".png"},partnumber:{$regex:"OEM"}}



function () {
        var dataTable = $('#treetable').DataTable()
        dataTable.rows().select();
                                }



{ edrpath: { $exists: true}}



"id": "1",
"jobnumber": "keksieskdo",
"description": "dkdieksdoies",
"customer": "keksieskdo",
"user_id": "1",
"date_create": "2022-01-02 08:08:34.750696",
"date_due": " ",
"date_modify": " ",
"date_finish": " ",

"(?<oo>[a-zA-Z0-9_]+)": "(?<foo>[a-zA-Z0-9- :.]+)",
$1=StringField( $2 )



id=StringField( )
jobnumber=StringField( )
description=StringField( )
customer=StringField( )
user_id=StringField( )
date_create=StringField( )
date_due=StringField( )
date_modify=StringField( )
date_finish=StringField( )




(?<foo>"[.a-zA-Z0-9_-]+"):(?<o>"[,+-.a-zA-Z0-9_ ]+"),
$1['$2']


show dbs
use TinyMRP

db.part.deleteMany({  partnumber: RegExp('TMRP')})





allparts=mongoPart.objects()
paco=allparts(partnumber="AWS-A-010174")[0]
paco.updateFileset()
pepo=mongoFileSet(description="test")

allparts=mongoPart.objects()
for part in allparts: part.updateFileset()


allparts=mongoPart.objects()

for part in allparts:
    part.fileset=None
    part.save()


allparts=mongoPart.objects()
paco=allparts(partnumber="200366-GA")[0]

test['children']


paco.get_components()



import pymongo
import csv

client = pymongo.MongoClient("localhost", 27017)
db=client.TinyMRP
partcol=db["part"]

for part in partcol.find():
    partcol.update_one({"_id":part["_id"]},{"$unset":{"id":""}})




allparts=mongoPart.objects()
paco=allparts(partnumber="AWS-A-010174")[0]

parents=paco.getparents()
children=paco.getchildren()


pepe=allparts(partnumber="AWS-A-010176")[0]


paco.hasProcess("purchase")
paco.hasProcess("machine")
paco.hasConsumingProcess()



testpart=allparts[1]
testpart.getparents()



test=partcol.find_one({'partnumber':"OEM-TNM10W"})
parents=partcol.find({'children':{ '$elemMatch' :{'pk':test.pk}}})


test=mongoPart().objects(partnumber="OEM-TNM10W")




test=partcol.find({'pk':{'$in:'}})




allparts(description__icontains="bean")


allparts=allparts(Q(description__icontains="bean") & Q( description__icontains="pro"))




pipeline = [ {"$match": {}}, 
             {"$out": "part"},
]
mongodb.destination_collection.aggregate(pipeline)


sudo kill -9 $(sudo lsof -t -i:5000)




allparts=mongoPart.objects()
i=1
for part in allparts:
    if i<4500: 
        i=i+1
        part.delete()
        part.save()



allparts=mongoPart.objects()
i=1
for part in allparts:
        part.delete()
        part.save()
















def updateFileset(self,web=False,persist=False):
        self.get_tag()
        parttag=self.partnumber+"_REV_"+self.revision
        save=False

        fileset=[]
        for filetype in config['FILES_CONF'].keys():
            if config['FILES_CONF'][filetype]['list']=='yes':
                refdict=config['FILES_CONF'][filetype]
                refdict['filetype']=filetype
                fileset.append(refdict)
        filepairs=[]
        for filetype in fileset:
            if filetype['filetype'] in filelist:
                for i in range(6):
                    extension="extension"+str(i)
                    # print(type(filetype[extension]))
                    # print([filetype['filetype'],filetype['folder'],filetype[extension]])
                    if filetype[extension]!="" and type(filetype[extension])==str:

                        filepairs.append([filetype['filetype'],filetype['folder'],filetype[extension],filetype['filemod']])




        for filetype,folder,extension,filemod in filepairs: 
                filetag=config['DELIVERABLES'][filetype]['path']+parttag+str(config['DELIVERABLES'][filetype]['filemod'])+"."+extension
                
                if file_exists(filetag):
                    if config['DELIVERABLES'][filetype]['list']!="yes":
                        # try:
                            if self[filetype+'path']!=filetag:
                                self[filetype+'path']=filetag
                                # #print(filetype,extension)
                                # #print("string- " ,filetag)
                                save=True
                        # except:
                        #     #print("couldnt save - ", "string- " ,filetag)
                        #     pass
                    # else:
                    #     if self[filetype+'path']==[] or self[filetype+'path']==None:
                    #         self[filetype+'path']=[]

                    #     if not ( filetag in self[filetype+'path'] ):
                    #         try:
                    #             self[filetype+'path'].append(filetag)
                    #         # #print(filetype,extension)
                    #         # #print("list- ", filetag)
                    #             save=True
                    #         except:
                    #             pass
                    #             # print("issues finding tag for ",self[filetype+'path'])
                else:
                    if filetype=='qr':
                         qrcode=qr_code(self,filename=filetag)
                         self['qrpath']=qrcode
                        #  print("before qqqqqqqqqrrrrrrrrrr",self['qrpath'])
                         self.save() 
                    
                    # if filetype+'path'=='pngpath':
                    #     self[filetype+'path']=url_for('static', filename='images/logo.png')
                    #     save=True

 
                if web:
                    try:
                        self[filetype+'path']=self[filetype+'path'].replace(fileserver_path,webfileserver)

                    except:
                        pass

        if self['pngpath']=="" or self['pngpath']==None or self['pngpath']=="/static/images/logo.svg":
            self['pngpath']=webfileserver+'/logo.png'
            self.save()            
            # print(self['pngpath'])

        
        if persist:
            # print("later qqqqqqqqqrrrrrrrrrr",self['qrpath'])
            if save: self.save()




//Extraction of selected rows for fileset compilation
  $("#fileset-dt").click(function () {
    var dataTable = $('#treetable').DataTable()
    var rowsel= dataTable.rows( { selected: true } );
    var alldata=[]
    var filelist=[]

    for (let i = 0; i < fileset.length; i++) {
                // console.log( fileset[i]);
                var dicto={checkbox:"#"+fileset[i]['filetype']+"_cb"};
                var filecheck="#"+fileset[i]['filetype']+"_cb";        
                var checkcheckbox=document.querySelector(filecheck).checked;
                if( checkcheckbox == true ){filelist.push(fileset[i]['filetype'])}       
        }

    rowsel.data(1).each( function () {
                alldata=[];
                $(this).each( function () {alldata.push($(this)[0])  } );
        } );

    $.ajax({
                type: "POST",
                url: '/vault/api/listfileset',
                dataType: "json",
                data: {'alldata':testdata, 'filelist':fileout},
                success: function(response) {
                    if(  response != "" ){
                    window.location = response;}
                    else{alert("No parts or files selected to extract")}},
                error: function(error) {
                    console.log(error)
                }
         });


  });











<a href="/vault/part/detail/quick:AWS-Z-009404_rev_%2525"><img src='http://192.168.1.21:8888/Deliverables/png/AWS-Z-009404_REV_.png' width=auto height=30rm></a>.












{
                        text: "Toggle Top level only/full BOM",
                        action: function() {
                            if (level == "yes") {
                                level = "no";
                                document.getElementById("level").innerHTML = "TOP LEVEL ONLY";
                                document.getElementById("level").style.background = "green";
                            } else {
                                level = "yes";
                                document.getElementById("level").innerHTML = "FULL BOM";
                                document.getElementById("level").style.background = "orange";
                            }

                            $("#treetable").DataTable().ajax.reload();
                        },
                    },
                    {
                        text: "Toggle Flat/Treee BOM",
                        action: function() {
                            if (structure == "tree") {
                                structure = "flat";
                                $("#treetable").DataTable().column(0).visible(false);
                                dataTable.column(8).visible(false);
                                dataTable.column(9).visible(false);
                                document.getElementById("structure").innerHTML = "FLAT BOM";
                                document.getElementById("structure").style.background = "orange";
                            } else {
                                structure = "tree";
                                $("#treetable").DataTable().column(0).visible(true);
                                dataTable.column(8).visible(true);
                                dataTable.column(9).visible(true);
                                document.getElementById("structure").innerHTML = "TREE BOM";
                                document.getElementById("structure").style.background = "green";
                            }

                            $("#treetable").DataTable().ajax.reload();
                        },
                    },
                    {
                        text: "Toggle Show/Hide Consumed",
                        action: function() {
                            console.log(consume);
                            if (consume == "no") {
                                consume = "yes";
                                document.getElementById("consume").innerHTML = "SHOWN";
                                document.getElementById("consume").style.background = "green";
                            } else {
                                consume = "no";
                                document.getElementById("consume").innerHTML = "HIDDEN";
                                document.getElementById("consume").style.background = "orange";
                            }

                            $("#treetable").DataTable().ajax.reload();
                            console.log(consume);
                        },
                    },