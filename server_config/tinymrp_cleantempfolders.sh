#!/bin/bash

tinyfolder="/TinyMRP"
filefolder="/Fileserver"

tinytemp="/TinyMRP/TinyWEB/temp"
filetemp="/Fileserver/Deliverables/temp"

chmod -R 777 /Fileserver/Deliverables/
chmod -R 777 /TinyMRP/

rm -r $tinytemp/*
rm -r $filetemp/*



