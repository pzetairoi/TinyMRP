#!/bin/bash

package_list="nginx git samba python3 net-tools python3-venv wormhole"
deliverables="3mf,datasheet,dxf,edr,pdf,pic,png,reports,step,temp"
tinyfolder="/TinyMRP"
filefolder="/Fileserver"
repository="pzetairoi/TinyMRP.git"
<<<<<<< HEAD
#removed login line for avoiding issues with github
=======
#removed gitlogin line for avoiding issues with github
>>>>>>> 6b18a49... Added initial files from home install at 04-06-2024



#apt-get update 
apt-get install -y  $package_list

#Create shared deliverables folder
cd /
mkdir $filefolder 
cd $filefolder
chmod -R 777 $filefolder

#for folder in $deliverables
for folder in {3mf,datasheet,dxf,edr,pdf,pic,png,reports,step,temp}
do
echo "created $folder"
mkdir $folder
done
#exit 0
chmod -R 777 $filefolder



#Create repository folder and clone it
cd /
mkdir $tinyfolder
mkdir $tinyfolder/TinyWEB/TinyWEB/data
chmod -R 777 $tinyfolder
git clone https://$git_login@github.com/$repository $tinyfolder


#To update repository
cd $tinyfolder
git pull

#copy the original database and conf file if not present

inFILE="/TinyMRP/server_config/TinyMRP_conf.xlsm"
outFILE="/TinyMRP/TinyWEB/TinyWEB/data/TinyMRP_conf.xlsm"

if test -f $outFILE; then
	echo "config exists"
else 
	cp $inFILE $outFILE
fi



inFILE="/TinyMRP/server_config/TinyMRP.db"
outFILE="/TinyMRP/TinyWEB/TinyWEB/data/TinyMRP.db"

if test -f $outFILE; then
        echo "config exists"
else
        cp $inFILE $outFILE
fi


#Create virtual enviroment
cd $tinyfolder 
python3 -m venv tinymrp_env 
source $tinyfolder/tinymrp_env/bin/activate 
pip install -r $tinyfolder/TinyWEB/requirements.txt
deactivate
cd /


#Configure Fileserver files Samba
cp /TinyMRP/server_config/smb.conf /etc/samba/
chmod -R 777 $filefolder
systemctl restart smbd.service


#Configure Nginx and copy the service
chmod -R 777 $tinyfolder
rm  /etc/nginx/nginx.conf

cp /TinyMRP/server_config/nginx.conf /etc/nginx/nginx.conf
cp /TinyMRP/server_config/tinymrp.conf  /etc/nginx/sites-available
ln -s /etc/nginx/sites-available/tinymrp.conf  /etc/nginx/sites-enabled/tinymrp.conf
rm  /etc/nginx/sites-enabled/default
cd /

cp  /TinyMRP/server_config/tinymrp_server.service  /etc/systemd/system/tinymrp_server.service

systemctl daemon-reload
systemctl restart nginx.service
systemctl restart tinymrp_server.service

