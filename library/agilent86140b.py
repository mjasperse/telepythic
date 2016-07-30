"""
AGILENT 86140B DATA EXTRACTOR
Extracts all currently visible traces from the Agilent 86140B optical spectrum analyser

Usage: ./agi86140b.py [filename]
    If specified, extracted data is saved to CSV called "filename"

Programming guide: http://cp.literature.agilent.com/litweb/pdf/86140-90069.pdf
"""

from telepythic import TelepythicDevice, PrologixInterface
import numpy as np
import sys
import time

# connect to device
bridge = PrologixInterface(gpib=23,host=15)
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
if dev.query('CALC:AVER:STAT?'):
    navg = dev.query('CALC:AVER:COUN?')
else:
    navg = 0

tr = {}
dev.write('FORM REAL,32')	# transfer data in binary (fast) mode
for i in 'ABCDEF':
    if dev.query('DISP:TRAC:STAT? TR'+i):
        print 'Downloading trace', i
        npts = dev.query('TRAC:POIN? TR'+i)           # number of points
        start = dev.query('TRAC:X:STAR? TR'+i)*1e9    # in nm
        stop = dev.query('TRAC:X:STOP? TR'+i)*1e9     # in nm
        X = np.linspace(start,stop,npts)
        Y = dev.ask_block('TRAC:DATA:Y? TR'+i,'>f4')  # NB: big endian data
        tr[i] = np.transpose([X,Y])

# we're done, return to local control
dev.close()

# Save it to a text file
if len(sys.argv) > 1:
    with open(sys.argv[1],'w') as f:
        print >> f, time.strftime('%Y%m%dT%H%M%S')
        print >> f, id
        print >> f, "RBW,", bw, ", RefLvl,", ref, ", Sens,", sens, ", Navg,", navg, '\n'
        print >> f, ', '.join(['TR'+i+'_X, TR'+i+'_Y' for i in tr])
        M = np.hstack(tr.values())
        np.savetxt(f, M, '%g', ', ', '\n')
        print "Saved to", f.name

# Make a plot:
import pylab as pyl
pyl.clf()
for i,XY in tr.items():
    pyl.plot(XY[:,0],XY[:,1],label='TR'+i)
pyl.legend()
pyl.xlabel('$\lambda$ (nm)')
pyl.axis('tight')
pyl.grid(True)
pyl.show()
