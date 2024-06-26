#Based on ubuntu 22.04 install
#sudo apt install ubuntu-desktop-minimal  -y

#Install Ngix git and samba
apt-get install -y nginx git samba gunicorn
cd ~

sudo mkdir /Fileserver
sudo mkdir /Fileserver/Deliverables
sudo mkdir /Fileserver/Deliverables/temp
sudo mkdir /Fileserver/Deliverables/temp/upload
sudo mkdir /Fileserver/Deliverables/png
sudo mkdir /Fileserver/System

#Share with full write access
 sudo chmod +777 /Fileserver
 sudo chmod +777  ~/Server/

sudo cp  ~/Server/TinyMRP/install/smb.conf /etc/samba/smb.conf 

sudo systemctl restart smbd.service



#INSTALL python stuff
sudo apt install python3-venv  python-pkg-resources -y

#Create the webserver folder files
mkdir ~/Server
cd ~/Server
git clone https://github.com/pzetairoi/TinyMRP.git
cd ~/Server/TinyMRP
cp TinyMRP_conf-template.xlsm TinyMRP_conf.xlsm
cp data-dev-template.sqlite data-dev.sqlite
mkdir ~/Server/TinyMRP/temp

#Virtual enviroment and libraries
pip install virtualenv
python3 -m venv venv

source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt




#Install Mongodb
sudo apt-get install gnupg curl -y
# curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
#    sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
#    --dearmor
# echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
# sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl enable mongod.service
sudo systemctl start mongod.service

#Modify the mongodb configuration with the repository one
sudo cp ~/Server/TinyMRP/install/mongod.conf /etc/mongod.conf
sudo systemctl restart mongod.service

#Copy initial database
sudo apt-get install unzip -y
cd ~/Server/TinyMRP
unzip TinyMRP_mongodb_template.zip -d /tmp/mongodb_backup
mongorestore --db TinyMRP --verbose /tmp/mongodb_backup/TinyMRP
rm -rf /tmp/mongodb_backup


#Copy generic image logo to Fileserver/System
cd ~/Server/TinyMRP
sudo cp app/static/images/logo.png /Fileserver/System/logo.png



#Configure Nginx and copy the service

#sudo rm  /etc/nginx/nginx.conf

#sudo cp ~/Server/TinyMRP/install/nginx.conf /etc/nginx/nginx.conf
sudo cp ~/Server/TinyMRP/install/tinymrp.conf   /etc/nginx/sites-available
sudo cp ~/Server/TinyMRP/install/fileserver.conf   /etc/nginx/sites-available
sudo ln -s /etc/nginx/sites-available/tinymrp.conf  /etc/nginx/sites-enabled/tinymrp.conf
sudo ln -s /etc/nginx/sites-available/fileserver.conf  /etc/nginx/sites-enabled/fileserver.conf
sudo rm  /etc/nginx/sites-enabled/default


sudo cp  ~/Server/TinyMRP/install/tinymrp_server.service  /etc/systemd/system/tinymrp_server.service 


sudo chmod +777 ~/Server/TinyMRP/

sudo systemctl daemon-reload
sudo systemctl restart nginx.service
sudo systemctl restart tinymrp_server.service


sudo systemctl enable tinymrp_server.service





-----------------------------------------------
Previous
-----------------------------------------------








#-------------------------------------------
#Install mongo DEB

#Install the pdfkit and ubuntu packages
Step1: Download library pdfkit
 $ pip install pdfkit
Step2: Download wkhtmltopdf
For Ubuntu/Debian:
 sudo apt-get install wkhtmltopdf




#Add crontab scheduled erase temp folders using the default user (tinymrp)
crontab -e 
#option 1 for nano
#Every week at sudnay midnight the temp files will be erased
0     0       *       *       0       /TinyMRP/server_config/tinymrp_cleantempfolders.sh


##Add crontab scheduled update repository using the sudo user (sudo with tinymrp)
#update once per WEEK at 00:01 every sunday at midnight
#option 1 for nano
sudo crontab -e
1     0       *       *       0       /TinyMRP/server_config/tinymrp_update.sh



#To change the timezone
sudo timedatectl set-timezone Australia/Victoria



##################################################
###### Anydesk - remote desktop #######
##################################################

sudo apt update
sudo apt install wget -y
wget -qO - https://keys.anydesk.com/repos/DEB-GPG-KEY | sudo apt-key add -
echo "deb http://deb.anydesk.com/ all main" | sudo tee /etc/apt/sources.list.d/anydesk-stable.list
sudo apt update
sudo apt install anydesk -y

##################################################
##################################################




##################################################
###### Backup TinyMRP and system #######
##################################################
###TinyMRP backup every day
#Just backing up the database with deja-dup (has graphical interface)
#https://adamtheautomator.com/ubuntu-backup/

sudo snap install deja-dup --classic

#Then use it to backup the TinyMRP folder every day




#### System Backup every week
## Add the repository to apt-get to make it available to download
sudo add-apt-repository ppa:teejee2008/ppa

## Download all available packages
sudo apt update

## Download and install the Timeshift package
sudo apt install timeshift

#Then use it to backup the system every week 

##################################################
##################################################
