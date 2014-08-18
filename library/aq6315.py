"""
AQ6315E DATA EXTRACTOR
Extracts all visible traces from Ando AQ-6315E Optical Spectrum Analyser

Usage: ./aq6315.py [filename]
    If specified, extracted data is saved to CSV called "filename"

Relevant list of commands available at
    http://support.us.yokogawa.com/downloads/TMI/COMM/AQ6317B/AQ6317B%20R0101.pdf
        > GPIB commands, section 9
        > Trace query format, section 9-42
"""

import sys
from telepythic import TelepythicDevice, PrologixInterface
import numpy as np
import pandas as pd
import pylab

# connect to device
bridge = PrologixInterface(gpib=1,host=177,timeout=0.5)
dev = TelepythicDevice(bridge)
# confirm device identity
id = dev.id(expect='ANDO,AQ6315')
print 'Device ID:',id

res = dev.query('RESLN?')   # resolution
ref = dev.query('REFL?')    # reference level
npts = dev.query('SEGP?')   # number of points in sweep
expectedlen = 12*npts+8     # estimate size of trace (ASCII format)

def get_trace(cmd):
    # device returns a comma-separated list of values
    Y = dev.ask(cmd).strip().split(',')
    # first value is an integer, listing how many values follow
    n = int(Y.pop(0))
    # check that it matches what we got (i.e. no data was lost)
    assert len(Y) == n, 'Got '+str(len(Y))+' elems, expected '+str(n)
    # convert to a numpy array
    return np.asarray(Y,'f')

pylab.clf()
res = {}
for t in 'ABC':                             # device has 3 traces
    if dev.ask('DSP'+t+'?'):                # if the trace is visible
        print 'Reading Trace',t             # download this trace
        res[t+'V'] = get_trace('LDAT'+t)    # download measurement values (Y)
        res[t+'L'] = get_trace('WDAT'+t)    # download wavelength values (X)
        pylab.plot(res[t+'L'],res[t+'V'])   # plot results

# convert results dict to a pandas dataframe
df = pd.DataFrame(res)
if len(sys.argv) > 1:
    # write to csv if filename was specified
    df.to_csv(sys.argv[1],index=False)

# close connection to prologix
dev.close()
# show graph
show()
