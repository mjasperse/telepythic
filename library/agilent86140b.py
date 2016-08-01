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
		
	def get_pcl(self):
		"""Download a PCL file from the unit **TESTING ONLY**"""
		# set into PCL output mode
		self.write('HCOPY:DEV:LANG PCL')
		# make sure it worked
		assert self.ask('HCOPY:DEV:LANG?') == 'PCL'
		# request the data
		self.write('HCOPY:DATA?')
		# it needs some time to generate the file before it outputs
		time.sleep(3)
		# response is an INDEFINITE length binary block reponse
		if self.bstream:	# we're using a bridge, this is a problem
			# check the response is of the right form
			assert self.read_raw(2) == '#0', 'Expected indefinite block response'
			# accumulate data until we stop getting fed it
			data = ''
			while self.dev.has_reply(timeout=1):
				data = data + dev.read()
		else:				# we're using VISA so we have a real EOI flag
			# read raw data until EOI
			data = self.dev.read_raw()
			# check header
			assert data[:2] == '#0', 'Expected indefinite block response'
			# return the rest
			data = data[2:]
		# there's a newline at the end that's unnecessary
		return data[:-1]


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
