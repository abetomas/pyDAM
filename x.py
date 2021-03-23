import subprocess
import datetime
import sys
import os

ToDir='./'
l = 'x x x'

dtstamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
head, tail = os.path.split(sys.argv[0])
logf = tail + '_' + dtstamp + '.log'

print(logf)

subprocess.run(['echo "' + tail + ' logfile=[' + logf + ']" >> ' + logf], shell=True)
subprocess.run(['echo "**********" >> ' + logf], shell=True)

subprocess.run(['echo ' + l + ' >> ' + ToDir + logf], shell=True)
