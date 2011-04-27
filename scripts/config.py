#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	config.py
	General config file to upload data with FTP
"""
import os

ftp_host="ftp.leretourdelautruche.com"	# your ftp server
ftp_user="xxx"	# your ftp use login
ftp_password="xxx"	# your ftp user password
ftp_directory="/www/map/cctv"	# the directory (on ftp) to put data

home=os.path.expanduser("~")
osm_data_folder="%s/osm/data/" % home
osm_temp_folder="%s/osm/data/temp/" % home