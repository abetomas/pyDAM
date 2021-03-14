# FileImg.py
"""
usage: FileImg.py [-h] [-log] SOURCE DESTINATION

Organize image files by capture date.
  This utility retrieves all image files from [SOURCE] folder directory and it's sub-directories.
  Image files are moved to [DESTINATION] folders based on image capture date and organized into YYYY/YYYY-MM-DD folders.
  Duplicated files will not be moved to the new folders.
  Files with no image capture date are stored in the folder [DESTINATION]/No-Capture-Date.

positional arguments:
  SOURCE       Source folder of images
  DESTINATION  Destination folder of images

optional arguments:
  -h, --help   show this help message and exit
  -log         Display log of actions done on each image file

This file utility uses Phil Harvey's excellent 'exiftool' application (https://exiftool.org) 
through the pyExifTool wrapper of Sven Marnach (https://smarnach.github.io/pyexiftool/)

written by: 
Abe Tomas, March 2021

"""

import os
import subprocess
import time
from datetime import timedelta
import sys
import argparse
# import datetime
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
loglist = []
duplist = []
PrintLog = False

def main(fromfolder='?', tofolder='?', log='y'):

    global FromDir, ToDir, PrintLog # from args
    FromDir, ToDir = GetFolders(FromDir, ToDir)

    print ('\n'+ sys.argv[0] + ' ..... processing .....')
    
    if not os.path.exists(ToDir):
        os.makedirs(ToDir)
        print('**> Destination folder ' + ToDir + ' created.')

    # create folder for files with no-capture-date
    if not os.path.exists(ToDir + '/No-Capture-Date'):
        os.makedirs(ToDir + '/No-Capture-Date')

    # retrieve *all image filenames  
    flist=get_dirlist(FromDir)

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
    # global PrintLog

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
                    loglist.append('IGNORED ***  : ' + entry.path)
                    ignctr += 1
                if PrintLog:
                    print (str(allctr) + ': ' + loglist[-1])

            if not entry.name.startswith('.') and entry.is_dir():
                dirlist.append(entry.path)
                dirlist += get_dirlist(entry.path)

    return filelist

def process_file (f):
    """
    global FromDir, ToDir
    global loglist, duplist
    """
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
                ToFileName = ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail
                if CreateDate == et.get_tag('CreateDate', (ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)):             
                    loglist.append('DUP FILE+DATE: ' + f + ' == ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
                    duplist.append(tail + ' * DUP FILE+DATE: ' + f + ' == ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
                    dupdctr += 1
                else:
                    loglist.append('DUP FILENAME : ' + f + ' == ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
                    duplist.append(tail + ' * DUP FILENAME   : ' + f + ' == ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
                    dupnctr += 1
                dupctr += 1
            else: 
                loglist.append('ADDED        : ' + f + ' +> ' + ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail)
                addctr += 1
                subprocess.run(['cp', '-pn', f, ToDir + '/' + OrigYYYY + '/' + CaptureDate]) 
                # subprocess.run(['touch', ToDir + '/' + OrigYYYY + '/' + CaptureDate + '/' + tail])        
        else: 
                
            if os.path.isfile(ToDir + '/No-Capture-Date/' + tail):
                loglist.append('NO-DATE DUP  : ' + f + ' == ' + ToDir + '/No-Capture-Date/' + tail)
                nddctr += 1
            else:
                loglist.append('NO-DATE ADD  : ' + f + ' +> ' + ToDir + '/No-Capture-Date/' + tail)
                ndactr += 1
                subprocess.run(['cp', '-pn', f, ToDir + '/No-Capture-Date/'])     
                # subprocess.run(['touch', ToDir + '/No-Capture-Date/' + '/' + tail])
            ndtctr += 1

def print_stats():

    # global addctr, dupctr, dupdctr, dupnctr, ignctr, allctr, imgctr, nddctr, ndactr, ndtctr
    if dupctr:
        print ('\n***** Duplicates *****')
        for d in duplist:
            print (d)
        print ('***** End of Duplicates list *****')

    print ("\nSource      [" + FromDir + "]")
    print ("Destination [" + ToDir + "]")
    print (
        'All Files=' + str(allctr)        
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

start_time = time.monotonic()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Organize image files by capture date."
        "\n  This utility retrieves all image files from [SOURCE] folder directory and it's sub-directories."
        "\n  Image files are moved to [DESTINATION] folders based on image capture date and organized into YYYY/YYYY-MM-DD folders."
        "\n  Duplicated files will not be moved to the new folders."
        "\n  Files with no image capture date are stored in the folder [DESTINATION]/No-Capture-Date."
        ,formatter_class=argparse.RawDescriptionHelpFormatter
        )
    parser.add_argument('SOURCE',type=str,help='Source folder of images')
    parser.add_argument('DESTINATION',type=str,help='Destination folder of images')
    parser.add_argument('-log',action='store_true',help='Display log of actions done on each image file')    
    args = parser.parse_args()
    FromDir=args.SOURCE
    ToDir=args.DESTINATION
    PrintLog=args.log

    main()

end_time = time.monotonic()
print('\nElapsed Time: ',timedelta(seconds=end_time - start_time))
print ('***** Done! *****\n') 
