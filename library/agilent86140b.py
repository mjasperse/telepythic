"""
AGILENT 86140B DATA EXTRACTOR
Extracts all currently visible traces from the Agilent 86140B optical spectrum analyser

Usage: ./agi86140b.py [filename]
    If specified, extracted data is saved to CSV called "filename"

Programming guide: http://cp.literature.agilent.com/litweb/pdf/86140-90069.pdf
"""

from telepythic import TelepythicDevice, PrologixInterface
import sys, time
import numpy as np

# connect to device
bridge = PrologixInterface(gpib=23,host=177)
dev = TelepythicDevice(bridge)
# confirm device identity
id = dev.id('AGILENT,86140B')
print 'Device ID:',id

# query information about run
bw = dev.ask('SENS:BAND:RES?')          # get RBW
ref = dev.ask('DISP:TRAC:Y:RLEV?')      # reference level
sens = dev.ask('POW:DC:RANG:LOW?')      # sensitivity
units = dev.ask('UNIT:POW?')            # unit of y-axis

# are we averaging?
if dev.ask('CALC:AVER:STAT?'):
    navg = dev.ask('CALC:AVER:COUN?')
else:
    navg = 0

tr = {}
dev.send('FORM REAL,32')
for i in 'ABCDEF':
    if dev.ask('DISP:TRAC:STAT? TR'+i):
        print 'Downloading trace', i
        npts = dev.ask('TRAC:POIN? TR'+i)           # number of points
        start = dev.ask('TRAC:X:STAR? TR'+i)*1e9    # in nm
        stop = dev.ask('TRAC:X:STOP? TR'+i)*1e9     # in nm
        X = np.linspace(start,stop,npts)
        dev.write('TRAC:DATA:Y? TR'+i)
        Y = dev.read_block('f4')
        tr[i] = np.transpose([X,Y])

# we're done, return to local control
dev.close()

# Save it to a text file
if len(sys.argv) > 1:
    with open(sys.argv[1],'w') as f:
        print >> f, time.strftime('%Y%m%dT%H%M%S')
        print >> f, dev.id
        print >> f, "BW,", bw, ", Ref,", ref, ", Sens,", sens, ", Navg,", navg, '\n'
        print >> f, ', '.join(['TR'+i+'_X, TR'+i+'_Y' for i in tr])
        M = np.hstack(tr.values())
        np.savetxt(f, M, '%g', ', ', '\n')

# Make a plot:
from pylab import *
clf()
for i,XY in tr.items():
    plot(XY[:,0],XY[:,1],label='TR'+i)
legend()
xlabel('$\lambda$ (nm)')
axis('tight')
grid(True)
show()
