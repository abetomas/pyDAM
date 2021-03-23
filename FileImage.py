# FileImage.py
"""
usage: FileImage.py [-h] [-log] SOURCE DESTINATION

Organize image files by capture date.
  This utility retrieves all image files from [SOURCE] folder directory and it's sub-directories.
  Image files are moved to [DESTINATION] folders based on image capture date and organized into YYYY/YYYY-MM-DD folders.
  Duplicated files will not be moved to the new folders.
  Files with no image capture date are stored in the folder [DESTINATION]/No-Capture-Date.
  The action done on each file is recorded in a logfile.

positional arguments:
  SOURCE       Source folder of images
  DESTINATION  Destination folder of images

optional arguments:
  -h, --help   show this help message and exit
  -log         Display log of actions done on each image file

This file utility uses Phil Harvey's excellent 'exiftool' application (https://exiftool.org) 
and the pyExifTool wrapper of Sven Marnach (https://smarnach.github.io/pyexiftool/)

written by: 
Abe Tomas, March 2021

"""

import os
import subprocess
import time
from datetime import timedelta
import datetime
import sys
import argparse
import re
import exiftool

# Global variables
ftype = '.HEIC$|.JPG$|.JPEG$|.ARW$|.DNG$|.m4v$|.NEF$|.MOV$|.MP4$|.TIFF$|.PNG$'
# ftype='.JPG$|.m4v$|.NEF$|.MOV$'

global addctr, dupctr, dupdctr, dupnctr, ignctr, allctr, imgctr, nddctr, ndactr, ndtctr
ignctr = 0
dupctr = 0
dupdctr = 0
dupnctr = 0
addctr = 0
allctr = 0
imgctr = 0
nddctr = 0
ndactr = 0
ndtctr = 0
filelist = []
ShowLog = False

# def main(fromfolder='?', tofolder='?', log='y'):
def main():

    global FromDir, ToDir, ShowLog # from args
    global logfile
    FromDir, ToDir = GetFolders(FromDir, ToDir)

    print ('\n'+ sys.argv[0] + ' ..... processing .....')

    if not os.path.exists(ToDir):
        os.makedirs(ToDir)
        print('**> Destination folder ' + ToDir + ' created.')

    # create logfile [progname_yyyymmd-hhmmss.log]
    dtstamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    head, tail = os.path.split(sys.argv[0])
    logfile = ToDir + '/' + tail + '_' + dtstamp + '.log'

    subprocess.run(['echo "' + tail + ' logfile (' + logfile + ')" >> ' + logfile], shell=True)
    subprocess.run(['echo "**********" >> ' + logfile], shell=True)
    
    # create folder for files with no-capture-date
    if not os.path.exists(ToDir + '/No-Capture-Date'):
        os.makedirs(ToDir + '/No-Capture-Date')

    # retrieve *all image filenames  
    # flist=get_dirlist(FromDir)
    get_dirlist(FromDir)

    print_stats()

def GetFolders (FromDir, ToDir):
    ok=False
    while not ok:
        # future: handle embeddded spaces in folder names
        # FromDir=input('From Folder : ')
        # ToDir=input('To Folder   : ')
        k=input("\nSource [" + FromDir + "]   Destination [" + ToDir + "]\n>> ok to continue (Y/N/Q)? ")
        k=input("SOURCE [" + FromDir + "]   DESTINATION [" + ToDir + "]  >> ARE YOU SURE (Y/N/Q)? ")      
        if k.lower() == 'y':
            if os.path.exists(FromDir):
                ok = True
            else:
                print("SOURCE [" + FromDir + "] does not exist.  Please try again.\n")
                os._exit(1)
        else:
            if k.lower() == 'q':
                print("'Q'uit accepted, ... goodbye .....\n")
                os._exit(1)
    if not os.path.exists(ToDir):
        os.makedirs(ToDir)
    
    return (FromDir, ToDir)

def get_dirlist(rootdir):
    # traverse directory tree and retrieve all image filenames
    global imgctr, ignctr, allctr

    dirlist = []
    with os.scandir(rootdir) as rit:
        for entry in rit:

            if not entry.name.startswith('.') and entry.is_file():
                head, tail = os.path.split(entry.path)
                allctr += 1
                if (re.search(ftype,tail,re.IGNORECASE)):
                    filelist.append(entry.path)
                    process_file(entry.path)
                    imgctr += 1
                else:
                    # not a valid image filetype      
                    ignctr += 1
                    logger('IGNORED ***  : ' + entry.path)
            if not entry.name.startswith('.') and entry.is_dir():
                dirlist.append(entry.path)
                dirlist += get_dirlist(entry.path)

    return filelist

def process_file (f):

    global addctr, dupctr, dupdctr, dupnctr, ignctr, allctr, imgctr, nddctr, ndactr, ndtctr
    with exiftool.ExifTool() as et:
        # print (f)
        # CaptureDate = et.get_tag('EXIF:DateTimeOriginal', f)
        CreateDate = et.get_tag('CreateDate', f)
        head, tail = os.path.split(f)
        if CreateDate:
            CaptureDate = re.sub(':','-',CreateDate[:10])
            OrigYYYY = CaptureDate[:4]
            # create directories based on creation dates
            if not os.path.exists(ToDir + '/' + OrigYYYY):
                os.makedirs(ToDir + '/' + OrigYYYY)
            if not os.path.exists(ToDir + '/' + OrigYYYY + '/' + CaptureDate):
                os.makedirs(ToDir + '/' + OrigYYYY + '/' + CaptureDate)

            # copy -noclobber file to destination
            if os.path.isfile(ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail):
                # file exists, therefore it's a duplicate
                dupctr += 1                
                if CreateDate == et.get_tag('CreateDate', (ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)):             
                    dupdctr += 1
                    logger('DUP FILE+DATE: ' + f + ' == ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
                    # duplist.append(tail + ' * DUP FILE+DATE: ' + f + ' == ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
                else:
                    dupnctr += 1                    
                    logger('DUP FILENAME : ' + f + ' == ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
                    # duplist.append(tail + ' * DUP FILENAME   : ' + f + ' == ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
            else: 
                addctr += 1
                logger('ADDED        : ' + f + ' +> ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
                subprocess.run(['cp', '-pn', f, ToDir + '/' + OrigYYYY + '/' + CaptureDate]) 
        else:   
            ndtctr += 1              
            if os.path.isfile(ToDir + '/No-Capture-Date/' + tail):
                nddctr += 1                
                logger('NO-DATE DUP  : ' + f + ' == ' + ToDir + '/No-Capture-Date/' + tail)
            else:
                ndactr += 1
                logger('NO-DATE ADD  : ' + f + ' +> ' + ToDir + '/No-Capture-Date/' + tail)
                subprocess.run(['cp', '-pn', f, ToDir + '/No-Capture-Date/'])     

def print_stats():

    print (
        "\nSource:      " + FromDir
        ,"\nDestination: " + ToDir
        ,"\nLogfile:     " + logfile
        )    
    print (
        '\nAll Files=' + str(allctr)        
        ,'\nImage-Files=' + str(imgctr)        
        ,'\n- Added=' + str(addctr)
        ,'\n- Duplicates=' + str(dupctr) 
        ,': Same-Date=' + str(dupdctr)
        ,' Same-File-Name=' + str(dupnctr)
        ,'\n- No-Capture-Date=' + str(ndtctr) 
        ,': Added=' + str(ndactr)
        ,' Same-File-Name=' + str(nddctr)
        ,'\nIgnored=' + str(ignctr)
        )   

    if dupctr:
        # there are duplicates that must be listed
        print ("\n*** Warning - DUPLICATES FOUND!"
            ,"\n    please >>> grep 'DUP' " + logfile + " <<< for duplicated files")

def get_parms ():

    global FromDir, ToDir, ShowLog
    parser = argparse.ArgumentParser(
        description="Organize image files by capture date."
        "\n  This utility retrieves all image files from [SOURCE] folder directory and it's sub-directories."
        "\n  Image files are moved to [DESTINATION] folders based on image capture date and organized into YYYY/YYYY-MM-DD folders."
        "\n  Duplicated files will not be moved to the new folders."
        "\n  Files with no image capture date are stored in the folder [DESTINATION]/No-Capture-Date."
        "\n  The action done on each file is recorded in a logfile."
        ,formatter_class=argparse.RawDescriptionHelpFormatter
        )
    parser.add_argument('SOURCE',type=str,help='Source folder of images')
    parser.add_argument('DESTINATION',type=str,help='Destination folder of images')
    parser.add_argument('-log',action='store_true',help='Display log of actions done on each image file')    
    args = parser.parse_args()
    FromDir=args.SOURCE
    ToDir=args.DESTINATION
    ShowLog=args.log

def logger (action):

    global logfile, ShowLog

    action=(str(allctr) + '. ' + action)
    if ShowLog:
        print(action)
    subprocess.run(['echo "' + action +  '" >> ' + logfile], shell=True)

##########################
if __name__ == "__main__":

    get_parms()

    start_time = time.monotonic()

    main()

    end_time = time.monotonic()
    print('\nElapsed Time: ',timedelta(seconds=end_time - start_time))
    print ('***** Done! *****\n') 
