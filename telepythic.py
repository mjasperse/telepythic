"""
TELEPYTHIC -- a python interface to test equipment
Copyright 2014 by Martijn Jasperse
https://bitbucket.org/martijnj/telepythic
"""
import numpy as np

class TelepythicDevice:
    def __init__(self,interface):
        """
        Create a device instance using the provided interface.
        
        The interface can be any class that provides the following functions:
            read(), read_raw(), write()
        """
        self.dev = interface
        self.bstream = getattr(interface,'bstream',True) and not hasattr(interface,'visalib')
    
    def __del__(self):
        """Destructor, attempts to close connection to the device"""
        try:    self.close()
        except: pass
    
    def id(self,expect=None,match_case=True):
        """Return the response to the *IDN? query. To ensure you're communicating with the device you expect, specify an "expect" string which is matched against the _start_ of the IDN response"""
        id = self.ask('*IDN?')
        if expect is not None:
            if not match_case:
                id = id.upper()
                expect = expect.upper()
            if not id.startswith(expect):
                raise RuntimeError('Expected ID '+repr(expect)+', got '+repr(id))
        return id
    
    def read_block(self,format=None):
        """Read a GPIB-style block of binary data from the device. If "format" is specified, the data is reinterpreted as a 1D numpy array with the corresponding dtype.
        
        GPIB block data is a binary stream of the form:
            #    - the ASCII character "#"
            N    - the size of following length string (single ASCII digit)
            M..M - number of bytes in the following data string (N-digits of ASCII)
            X..X - the actual data string (M bytes of binary data)
        """
        if not self.bstream:
            # NB: When using pyvisa, multiple sequential read_raw() commands are not permitted to
            # parse *part* of a response. If the "size" argument does not match the length of the
            # response (as defined by the EOM), an error is raised.
            # Hence we must read the *entire* raw response in, then parse it in sections.
        	data = self.read_raw(None)
        	head = data[:2]
        	assert head[0] == '#', 'Not a binary block array'
        	hlen = int(data[1])
        	dlen = int(data[2:2+hlen])
        	assert len(data) - (2+hlen+dlen) <= 2, 'Invalid block length'
        	data = data[2+hlen:2+hlen+dlen]
        else:
            # We don't know in advance how long the response is so consume piece by piece
        	head = self.read_raw(2)
        	assert head[0] == '#', 'Not a binary block array'
        	dlen = int(self.read_raw(int(head[1])))
        	data = self.read_raw(dlen)
        if format is None:
        	return data
        return np.fromstring(data,dtype=format)
    
    def parse_reply(self, x):
        """Interpret the reply string and return an appropriately type-cast value"""
        x = x.strip()
        try:    return int(x)
        except: pass
        try:    return float(x)
        except: pass
        if x[0] == '"': return x[1:x.rfind('"')]
        return x
    
    def ask(self, query, size=None):
        """A helper function that writes the command "query" and reads the reply. If "size" is not None, the response is assumed to be a binary string of that length"""
        self.dev.write(query)
        if size is None:
            return self.dev.read()
        else:
            return self.dev.read_raw(size)
    
    def query(self, query):
        """A helper function that asks "query" and returns the response. "query" can be a vector, in which case a dictionary of responses is returned."""
        if isinstance(query,str):
            # ensure query string contains a query
            if not '?' in query: query = query + '?'
            return self.parse_reply(self.ask(query))
        else:
            return { q: self.query(q) for q in query }
    
    def read(self):
        """Read data from the device (until EOM)"""
        return self.dev.read()
    
    def read_raw(self, size):
        """Read exactly "size" bytes from the device"""
        return self.dev.read_raw(size)
    
    def write(self, msg):
        """Write the specified string to the device"""
        return self.dev.write(msg)
    
    def flush(self):
        """Removes any pending response, returning the number of bytes flushed, or -1 if not supported by the device"""
        if hasattr(self.dev,"flush"):
            return self.dev.flush()
        return -1
    
    def close(self):
        """Close the connection to the associated device. Unlocks the device if the relevant command exists."""
        if hasattr(self,"lock"):
            self.lock(False)
        elif hasattr(self.dev,"lock"):
            self.dev.lock(False)
        if hasattr(self.dev,"close"):
            self.dev.close()


def pyvisa_connect(resource,timeout=1):
	"""Use pyvisa to connect to a VISA resource described by "resource", which may contain wildcards.
	The VISA communications timeout is "timeout", specified in seconds."""
	import pyvisa
	# query all available VISA devices
	rm = pyvisa.ResourceManager()
	# enumerate the USB devices
	devs = rm.list_resources(resource)
	# check there's only one
	if len(devs) == 0:
		raise RuntimeError("No VISA devices found")
	elif len(devs) > 2:
		raise RuntimeError("Specified VISA resource '%s' describes %i devices"%(resource,len(devs)))
	
	# open the device
	instr = rm.open_resource(devs[0])
	instr.timeout = timeout*1000 #ms
	return instr
