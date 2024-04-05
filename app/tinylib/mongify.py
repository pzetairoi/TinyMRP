#Add all the bom field
from unittest import skip
from app.tinylib.models import mongoPart


# for part in mongoPart.objects():
#     if part.bom==[] and len (part.children)>0:
#         for i in range(len(part.children)):
#             mongobom=mongoBom(part=part.children[i], qty=part.childrenqty[i])
#             part.bom.append(mongobom)
#             part.save()


#Clean mongodb of parts
for part in mongoPart.objects():
    part.delete()

for part in mongoPart.objects():
    part.bom=[]
    part.save()


#Copy all the parts

for litepart in Part.query.all():
    #print(litepart)
    dirtydict=litepart.__dict__
    #print(dirtydict)
    del dirtydict['_sa_instance_state']
    del dirtydict['id']
    #Process cleanup
    dirtydict['process']=[dirtydict['process'],dirtydict['process2'],dirtydict['process3']]
    del dirtydict['process2']
    del dirtydict['process3']
    #Revision to Mod wit the approved too
    # if litepart.revision=="" or litepart.revision==" ":
    #     dirtydict['revision']="MOD"    
    # if litepart.approved=="" and not "MOD" in dirtydict['revision']:
    #     dirtydict['revision']=dirtydict['revision']+"MOD"
    #print(dirtydict)
    partcol.insert_one(dirtydict)
db.session.flush()


for litepart in Part.query.all():
    mongopart=mongoPart.objects(partnumber=litepart.partnumber,revision=litepart.revision).first()
    mongopart.bom=[]
    for kid in litepart.children_with_qty():
        revision=kid.revision
        # if kid.revision=="" or kid.revision==" ":
        #     revision="MOD"
        # if kid.approved=="" and not ("MOD" in revision):
        #     revision=revision+"MOD"
        # mongokid=mongoPart.objects(partnumber=kid.partnumber,revision=revision).first()
        # if mongokid==None:
        #     mongokid=mongoPart.objects(partnumber=kid.partnumber,revision=revision+"MOD").first()
        # try:
        #     mongobom=mongoBom(part=mongokid,qty=kid.qty)
        #     mongopart.bom.append(mongobom)
        #     mongopart.save()
        # except:
        #     print("*****************",litepart)
        #     print("*****************",mongokid)
        mongokid=mongoPart.objects(partnumber=kid.partnumber,revision=revision).first()
        mongobom=mongoBom(part=mongokid,qty=kid.qty)
        mongopart.bom.append(mongobom)
        mongopart.save()



for part in mongoPart.objects():
    part.updateFileset(web=True,persist=True)






