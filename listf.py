# listf.py
# template program for traversing directory trees and retrieving file info
# AT 2021-02-24
# ref:
# https://stackoverflow.com/questions/973473/getting-a-list-of-all-subdirectories-in-the-current-directory/48833507#48833507
#

import os
import sys
import datetime

startdir=sys.argv[1] # start from this directory

def get_dirlist(rootdir):

    # dirlist = []

    with os.scandir(rootdir) as rit:
        for entry in rit:
            if not entry.name.startswith('.') and entry.is_file():
                info = entry.stat()	
                mstamp = datetime.datetime.fromtimestamp(info.st_mtime).strftime('%Y%m%d.%H:%M:%S')
                cstamp = datetime.datetime.fromtimestamp(info.st_birthtime).strftime('%Y%m%d.%H:%M:%S')
                head, tail = os.path.split(entry.path)
                print(
                    entry.path, 
                    # head, 
                    # tail, 
                    cstamp 
                    # mstamp
                    )
            if not entry.name.startswith('.') and entry.is_dir():
                # dirlist.append(entry.path)
                # dirlist += get_dirlist(entry.path)
                get_dirlist(entry.path)

    # dirlist.sort() # Optional, in case you want sorted directory names
    # return dirlist

get_dirlist(startdir)