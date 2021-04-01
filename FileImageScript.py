# FileImage.py
"""
usage: FileImage.py [-h] [-log] SOURCE DESTINATION

Organize image files by capture date.
  
  File utility to retrieve all image files from [SOURCE] directory and it's sub-directories.
  Generate a shell script for copying files to destination folders based on image capture date.
  Image files are organized into YYYY/YYYY-MM-DD folders.
  Files with no image capture date are stored in the folder [DESTINATION]/No-Capture-Date.
  The action done on each file is recorded in a logfile.
  Note:
  - The generated shell script (a kludge!) is intended to be executed within the NAS server, 
    this will bypass date-stamp issues on 'cp -p' flag when copying files on a WD MyCloud 
    EX2 Ultra NAS server from a MacOS Terminal.
  - See previous version 'FileImage.py' which actually copies files to destination folders.

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

# image filetypes
ftype = '.HEIC$|.JPG$|.JPEG$|.ARW$|.DNG$|.m4v$|.NEF$|.MOV$|.MP4$|.TIFF$|.PNG$'

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
ShowCtr = False

def main():

    global FromDir, ToDir, ShowLog # from args
    global logfile, copyscript, ShowCtr
    FromDir, ToDir = GetFolders(FromDir, ToDir)

    print ('\n'+ sys.argv[0] + ' ..... processing .....')

    # create logfile [progname_yyyymmd-hhmmss.log]
    dtstamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    head, tail = os.path.split(sys.argv[0])

    logfile = './' + tail + '_' + dtstamp + '.log'
    copyscript = './' + tail + '_' + dtstamp + '_cp.sh'    

    scripto('mkdir -v ' + ToDir)      
    if not os.path.exists(ToDir):
        os.makedirs(ToDir)
        print('**> Destination folder ' + ToDir + ' created.')

    logger('**********')    
    logger(tail + ' logfile(' + logfile + ')')
    logger('**********')
    ShowCtr = True

    # create folder for files with no-capture-date
    scripto('mkdir -v ' + ToDir + '/No-Capture-Date')                 
    if not os.path.exists(ToDir + '/No-Capture-Date'):
        os.makedirs(ToDir + '/No-Capture-Date')

    # retrieve *all image filenames  
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
                    imgctr += 1
                    filelist.append(entry.path)
                    process_file(entry.path)
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

        # CaptureDate = et.get_tag('EXIF:DateTimeOriginal', f)
        CreateDate = et.get_tag('CreateDate', f)
        head, tail = os.path.split(f)
        if CreateDate:
            CaptureDate = re.sub(':','-',CreateDate[:10])
            OrigYYYY = CaptureDate[:4]
            # create directories based on creation dates
            if not os.path.exists(ToDir + '/' + OrigYYYY):
                os.makedirs(ToDir + '/' + OrigYYYY)
                scripto('mkdir -v ' + ToDir + '/' + OrigYYYY)                     
            if not os.path.exists(ToDir + '/' + OrigYYYY + '/' + CaptureDate):
                os.makedirs(ToDir + '/' + OrigYYYY + '/' + CaptureDate)
                scripto('mkdir -v ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate)      
            # copy -noclobber file to destination
            addctr += 1                 
            scripto('cp -pnv ' + f + ' ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate) 
            logger('ADDED        : ' + f + ' +> ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)                                
        else:   
            ndtctr += 1              
            scripto('cp -pnv ' + f + ' ' + ToDir + '/No-Capture-Date/')                          
            logger('NO-DATE ADD  : ' + f + ' +> ' + ToDir + '/No-Capture-Date/' + tail)                    

def print_stats():

    global ShowCtr
    ShowCtr = False
    logger('**********')
    logger('Source:      ' + FromDir)
    logger('Destination: ' + ToDir)
    logger('Logfile:     ' + logfile)
    logger('cp script:   ' + copyscript)        
    logger(' ')    
    logger('All Files=' + str(allctr))    
    logger('- With-Capture-Date=' + str(addctr))
    logger('- Without-Capture-Date=' + str(ndtctr))    
    logger('Ignored=' + str(ignctr))

    print (
        "\nSource:      " + FromDir
        ,"\nDestination: " + ToDir
        ,"\nLogfile:     " + logfile
        ,"\ncp script:   " + copyscript        
        )    
    print (
        '\nAll Files=' + str(allctr)        
        ,'\nImage-Files=' + str(imgctr)        
        ,'\n- With-Capture-Date=' + str(addctr)
        ,'\n- Without-Capture-Date=' + str(ndtctr) 
        ,'\nIgnored=' + str(ignctr)
        )   

    subprocess.run(['chmod 755 ' + copyscript], shell=True)

def get_parms ():

    global FromDir, ToDir, ShowLog
    parser = argparse.ArgumentParser(
        description="Organize image files by capture date."
        "\n  "
        "\n  File utility to retrieve all image files from [SOURCE] directory and it's sub-directories."
        "\n  Generate a shell script for copying files to destination folders based on image capture date."
        "\n  Image files are organized into YYYY/YYYY-MM-DD folders."
        "\n  Files with no image capture date are stored in the folder [DESTINATION]/No-Capture-Date."
        "\n  The action done on each file is recorded in a logfile."
        "\n  Note:" 
        "\n  - The generated shell script (a kludge!) is intended to be executed within the NAS server, "
        "\n    this will bypass date-stamp issues on 'cp -p' flag when copying files on a WD MyCloud "
        "\n    EX2 Ultra NAS server from a MacOS Terminal."
        "\n  - See previous version 'FileImage.py' which actually copies files to destination folders."             
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

    global logfile, ShowLog, ShowCtr
    if ShowCtr:
        action=(str(allctr) + '. ' + action)
    if ShowLog:
        print(action)
    subprocess.run(['echo "' + action +  '" >> ' + logfile], shell=True)

def scripto (action):

    global copyscript
    subprocess.run(['echo "' + action +  '" >> ' + copyscript], shell=True)

##########################
if __name__ == "__main__":

    get_parms()

    start_time = time.monotonic()

    main()

    end_time = time.monotonic()

    elapsed=str(timedelta(seconds=end_time - start_time))
    logger(' ')
    logger('Elapsed Time: ' + elapsed)      
    logger('*** Done! ***')   
    logger(' ')

    print('\nElapsed Time: ', elapsed)
    print ('*** Done! ***\n') 
