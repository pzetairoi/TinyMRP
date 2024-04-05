!/bin/bash


package_list="nginx git samba python3 net-tools SSpython3-venv python3-flask wormhole"
deliverables="3mf datasheet dxf edr pdf pic png reports step temp"
tinyfolder="/home/tinymrp/tinymrp"
filefolder="/home/tinymrp/Fileserver/Deliverables"

echo $filefolder
repository="pzetairoi/TinyMRP.git"
<<<<<<< HEAD
#removed login line for avoiding issues with github
=======
#removed gitlogin line for avoiding issues with github
>>>>>>> 6b18a49... Added initial files from home install at 04-06-2024

#apt-get update 
apt-get install -y  $package_list

#Create shared deliverables folder
mkdir $tinyfolder
mkdir $filefolder 
cd $filefolder

#Create subfolders
mkdir $deliverables
chmod -R +777 $filefolder

#Create repository folder and clone it
cd /
mkdir $tinyfolder
#mkdir $tinyfolder/TinyWEB/TinyWEB/data
chmod -R +777 $tinyfolder
git clone https://$git_login@github.com/$repository $tinyfolder


#To update repository
cd $tinyfolder
git pull



#Create virtual enviroment 
#sudo -u tinymrp bash -c '\
#    python3 -m venv venv 
#    source $tinyfolder/venv/bin/activate 
#    pip install wheel
#    pip install -r $tinyfolder/requirements.txt
#    deactivate |\
#  bash
#'

tinyfolder="/home/tinymrp/tinymrp"
cd $tinyfolder 
python3 -m venv venv 
source $tinyfolder/venv/bin/activate 
pip install wheel
pip install -r $tinyfolder/slimreq.txt
deactivate




#Configure Fileserver files Samba
cp $tinyfolder/server_config/smb.conf /etc/samba/
chmod -R 777 $filefolder
systemctl restart smbd.service


#Configure Nginx and copy the service
chmod -R 777 $tinyfolder
rm  /etc/nginx/nginx.conf

cp $tinyfolder/server_config/nginx.conf /etc/nginx/nginx.conf
cp $tinyfolder/server_config/tinymrp.conf  /etc/nginx/sites-available
ln -s /etc/nginx/sites-available/tinymrp.conf  /etc/nginx/sites-enabled/tinymrp.conf
rm  /etc/nginx/sites-enabled/default


cp  $tinyfolder/server_config/tinymrp_server.service  /etc/systemd/system/newtinymrp_server.service 

systemctl daemon-reload
systemctl restart nginx.service
systemctl restart tinymrp_server.service


sudo systemctl enable tinymrp_server.service



