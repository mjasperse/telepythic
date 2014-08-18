"""
SR770 DATA EXTRACTOR
Extracts a trace from the Stanford Research SR770 FFT network analyser

Usage: ./sr770.py [filename]
    If specified, extracted data is saved to CSV called "filename"

See manual: http://www.thinksrs.com/downloads/PDFs/Manuals/SR770m.pdf (GPIB in  chapter 5)
"""

from telepythic import TelepythicDevice, PrologixInterface
import numpy as np
import sys, time

ascii_mode = False

# connect to device
bridge = PrologixInterface(gpib=5,host=175,timeout=2)
dev = TelepythicDevice(bridge)
# confirm device identity
id = dev.id(expect='Stanford_Research_Systems,SR770')
print 'Device ID:',id

# get the current span (see SR770 manual for array listing)
spans = [ 191e-3, 382e-3, 763e-3, 1.5, 3.1, 6.1, 12.2, 24.4, 48.75, 97.5, 195, 390, 780, 1.56e3, 3.125e3, 6.25e3, 12.5e3, 25e3, 50e3, 100e3 ]
span = spans[dev.ask('SPAN?'+trace)]
print 'Span = %g Hz' % span

# get units
units = [ 'Volts Pk', 'Volts RMS', 'dBV', 'dBVrms' ]
unit = units[dev.ask('UNIT?'+trace)]
print 'Units = ' + unit
disp = dev.ask('DISP?'+trace)

# check averaging
if dev.ask('AVGO?'):
    print 'Averaging = ON'
    navg = dev.sendrecv('NAVG?')
    print 'Number of averages =', navg
else:
    navg = 0

# number of bins is fixed (see manual)
nbins = 400

# get frequency
start = dev.ask('STRF?')
if dev.ask('XAXS?'+trace):
    # log in frequency
    freq = np.logspace(start, start + span, nbins)
else:
    # linear in frequency
    freq = np.linspace(start, start + span, nbins)

# get the spectrum
if ascii_mode:
    # comma-separated value list, comma at the end
    data = dev.ask('SPEC?'+trace, size=nbins*14)[:-1].split(',')
    assert len(data) == nbins
    spec = np.asarray(data,'f')
else:   # probably not working yet
    data = dev.ask('SPEB?'+trace, size=nbins*2)
    spec = np.fromstring(data,'<i2',count=nbins)
    fullscale = dev.ask('IRNG?')
    if disp == 0:   # logarithmic
        spec = (3.0103 * spec)/512.0 - 114.3914 + fullscale   # in dBV
    else:           # linear
        spec = spec / 32768.0 * fullscale
    
    
if len(sys.argv) > 1:
    # save it to a text file
    with open(sys.argv[1], 'w') as f:
        print >> f, id
        print >> f
        print >> f, "Freq (Hz), Power (%s)" % unit
        for x,y in zip(freq,spec):
            print >> f, x, y

import pylab
pylab.clf()
if unit.startswith('dB'):
    pylab.semilogy(freq,spec)
else:
    pylab.plot(freq,spec)
pylab.grid(True)
pylab.xlabel('Frequency (Hz)')
pylab.ylabel(unit)
pylab.axis('tight')
pylab.show()
