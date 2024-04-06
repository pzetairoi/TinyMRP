#This script is used to pull the latest code from the git repository and restart the server.
#!/bin/bash
cd ~/TinyMRP/SourceCode 
git pull
systemctl restart newtinymrp_server.service








