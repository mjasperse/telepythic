"""
TEKTRONIX OSCILLOSCOPE EXAMPLE
Shows how to connect to a TekTronix oscilloscope over USB using pyvisa, and download all visible channels to an H5 file
"""
import telepythic
from telepythic.library import tekscope

# look for USB instrument (will fail if there is more than one)
instr = telepythic.pyvisa_connect('USB?*::INSTR')
# connect to the instrument as an oscilloscope
scope = tekscope.TekScope(instr)
print 'Connected', scope.id().strip()

##### download the channels #####
import pylab as pyl
import numpy as np
import h5py
# create a new h5 file with the data in it
with h5py.File("scope.h5","w") as F:
	# find out what channels this scope has
	chans = scope.channels()
	for ch,col in zip(chans,'bgrkym'):
		# if the channel is enabled, download it
		if chans[ch]:
			print 'Downloading',ch
			wfmo, T, Y = scope.waveform(ch)
			# save it to the file
			D = F.create_dataset(ch,data=np.vstack([T,Y]).T)
			D.attrs.update(wfmo)
			# plot it
			pyl.plot(T,Y,col)
pyl.show()
