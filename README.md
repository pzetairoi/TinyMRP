# Initial Setup

## Check for Existing Files
 
Before making any changes, ensure you do not already have a TinyMRP_conf.xlsm file or a data-dev.sqlite database file that you wish to keep. If you do, make sure they are backed up or stored safely outside the repository folder.
Copy the Configuration and Database Templates

If TinyMRP_conf.xlsm or data-dev.sqlite do not exist, or you wish to reset them to the default templates, perform the following steps:

For the Configuration File:
cp TinyMRP_conf_template.xlsm TinyMRP_conf.xlsm

For the Database File:
cp data-dev-template.sqlite data-dev.sqlite

## Customize Your Configuration and Database
Configuration File:

Open TinyMRP_conf.xlsm in your preferred spreadsheet editor and adjust the settings to fit your local environment or personal preferences.

Database File:
The data-dev.sqlite file is a SQLite database that includes the generic starting logins:

## Windows dev version
You can run the debug version of tiny using win_requirements.txt and/or anaconda and the # conda_win_environment.yml file




### Admin login
admin@tinymrp.com pass:admin
### Project based login
test@test.com pass:test

To avoid accidentally tracking or pushing changes to TinyMRP_conf.xlsm and data-dev.sqlite, we've added them to the .gitignore file. This means Git will ignore changes to these files, keeping your local configurations safe from being overwritten by updates or affecting other users.

## Add the automatic update for the repository
Copy the file git-pull_template.sh and into git-pull.sh and edit it to put the actual folder of the installation

## Add the scrip to the cron tab

>crontab -e
> * * * * *   ~/TinyMRP/git-pull.sh



