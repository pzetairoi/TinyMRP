from os.path import exists

file_exists = exists(path_to_file)

allparts=db.session.query(Part)

for part in allparts:
    part.updatefilespath(fileserver_path)
    if exists(part.pngpath):
        #print(part.pngpath)
    else:
        deletepart(part,echo=True)





allparts=db.session.query(Part)

for part in allparts:
    part.updatefilespath(fileserver_path)
    if part.png:
        #print(part.pngpath)
    else:
        deletepart(part,echo=True)