import telepythic
from telepythic.library import tekscope

# open the device
instr = telepythic.pyvisa_connect('USB?*::INSTR')
scope = tekscope.TekScope(instr)
print 'Connected', dev.id()

import pylab as pyl
import numpy as np
import h5py

with h5py.File("scope.h5","w") as F:
	for c,col in zip(['CH1','CH2','CH3','CH4','REFA','REFB'],'bgrkym'):
		# check if this channel is visible
		if int(scope.ask('SEL:%s?'%c)):
			# download the data
			print 'Downloading',c
			wfmo, T, Y = scope.waveform(c)
			# save it to the file
			D = F.create_dataset(c,data=np.vstack([T,Y]).T)
			D.attrs.update(wfmo)
			# plot it
			pyl.plot(T,Y,col)
pyl.show()
