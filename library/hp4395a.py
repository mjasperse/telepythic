""" 
HP4395A DATA EXTRACTOR
Extracts a data trace from the HP 4395A network analyser

Usage: ./hp4935a.py [filename]

See commands list http://cp.literature.agilent.com/litweb/pdf/04395-90031.pdf
"""

from telepythic import TelepythicDevice, PrologixInterface
import sys, time

# use binary mode (fast), or ascii mode (slow)
BINARY_MODE = True

# connect to a prologix GPIB bridge
bridge = PrologixInterface(gpib=17,host=175,timeout=1)
# create a generic device instance
dev = TelepythicDevice(bridge)
# make sure the device is connect and identifies correctly
id = dev.id(expect=b"HEWLETT-PACKARD,4395A")

# interrogate settings
opts = dev.query([b'MEAS',b'BW',b'REFV',b'FMT',b'SWPT',b'SAUNIT',b'AVER',b'AVERFACT'])
assert opts[b'SWPT'] in (b'LINF',b'LOGF'), 'Unknown sweep mode'

# download trace
if BINARY_MODE:
	# binary mode is fast, but harder to debug
	dev.write(b'FORM3')          # 64-bit mode for data
	if fmt.startswith(b'SPEC'):  # spectrum analyser (real data)
		spec = dev.ask_block(b'OUTPDTRC?','f8')
	else:                       # VNA mode (imag part is auxiliary)
		spec = dev.ask_block(b'OUTPDTRC?','c16').real
	dev.write(b'FORM2')          # 32-bit mode for frequencies
	freq = dev.read_block(b'OUTPSWPRM?','f4')
else:
	import numpy as np
	dev.write(b'FORM4')  # ASCII mode
	specdat = dev.ask(b'OUTPDTRC?')
	spec = np.fromstring(specdat[1:],sep=',')
	freqdat = dev.ask(b'OUTPSWPRM?')
	freq = np.fromstring(freqdat[1:],sep=',')

# disconnect from device
dev.close()

# save it to a text file
if len(sys.argv) > 1:
	with open(sys.argv[1], 'w') as f:
		print >> f, id
		for k,v in opts.items():
			print >> f, k+',',v
		print >> f, "\nFreq (Hz),", opts[b'MEAS']
		for x, y in zip(freq,spec):
			print >> f, x, y;

# make a plot
import pylab
pylab.clf()
if opts[b'SWPT'] == b'LOGF':
	pylab.semilogx(freq,spec)
else:
	pylab.plot(freq,spec)
pylab.xlabel('f (Hz)')
pylab.ylabel(opts[b'MEAS'])
pylab.axis('tight')
pylab.grid(True)
pylab.show()
