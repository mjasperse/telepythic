"""
AGILENT 86140B DATA EXTRACTOR
Extracts all currently visible traces from the Agilent 86140B optical spectrum analyser

Usage: ./agi86140b.py [filename]
    If specified, extracted data is saved to CSV called "filename"

Programming guide: http://cp.literature.agilent.com/litweb/pdf/86140-90069.pdf
"""

from telepythic import TelepythicDevice, PrologixInterface
import numpy as np

class Agilent86140b(TelepythicDevice):
	"""Helper class for interfacing with Agilent 86140B optical spectrum analyser"""
	def __init__(self, interface):
		TelepythicDevice.__init__(self,interface)
		# confirm device identity
		self.id('AGILENT,86140B')
		
	def traces(self):
		"""Return a list of traces which are currently active"""
		return ['TR'+i for i in 'ABCDEF' if dev.query('DISP:TRAC:STAT? TR'+i)]
		
	def get_trace(self,trace=None):
		"""Download a trace of data from the unit"""
		if trace is None:		trace = ""
		elif len(trace) == 1:	trace = 'TR'+trace
		# create an array for wavelength values
		npts = self.query('TRAC:POIN? '+trace)
		start = self.query('TRAC:X:STAR? '+trace)*1e9    # in nm
		stop = self.query('TRAC:X:STOP? '+trace)*1e9     # in nm
		X = np.linspace(start,stop,npts)
		# download the spectrum in binary (fast) format
		self.write('FORM REAL,32')
		Y = self.ask_block('TRAC:DATA:Y? '+trace,'>f4')  # NB: big endian data
		# return a complete list
		return np.transpose([X,Y])


if __name__ == '__main__':
	import sys
	import time
	# connect to device
	bridge = PrologixInterface(gpib=23,host=15)
	dev = Agilent86140b(bridge)
	id = dev.id()
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

	# download all the data
	tr = {i: dev.get_trace(i) for i in dev.traces()}
	# we're done, return to local control
	dev.close()

	# Save it to a text file
	if len(sys.argv) > 1:
		with open(sys.argv[1],'w') as f:
			print >> f, time.strftime('%Y%m%dT%H%M%S')
			print >> f, id
			print >> f, "RBW,", bw, ", RefLvl,", ref, ", Sens,", sens, ", Navg,", navg, '\n'
			print >> f, ', '.join(['%s_X, %s_Y'%(i,i) for i in tr])
			M = np.hstack(tr.values())
			np.savetxt(f, M, '%g', ', ', '\n')
			print "Saved to", f.name

	# Make a plot
	import pylab as pyl
	pyl.clf()
	for i,XY in tr.items():
		pyl.plot(XY[:,0],XY[:,1],label=i)
	pyl.legend()
	pyl.xlabel('$\lambda$ (nm)')
	pyl.axis('tight')
	pyl.grid(True)
	pyl.show()
