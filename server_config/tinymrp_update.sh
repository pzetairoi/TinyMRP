#!/bin/bash
# This bash script will force the update of the tinymrp repository from github
package_list="nginx git samba python3 net-tools python3-venv wormhole"
deliverables="3mf,datasheet,dxf,edr,pdf,pic,png,reports,step,temp"
tinyfolder="/TinyMRP"
filefolder="/Fileserver"
repository="pzetairoi/TinyMRP.git"
#removed gitlogin line for avoiding issues with github

chmod -R 777 /TinyMRP/
chmod -R +x /TinyMRP/server_config/*

cd $tinyfolder
git reset --hard HEAD
git pull https://$git_login@github.com/$repository 
chmod -R 777 /TinyMRP/
chmod -R +x /TinyMRP/server_config/*
#sleep 2
systemctl daemon-reload
#sleep 2
systemctl restart nginx.service
#sleep 2
systemctl restart tinymrp_server.service





