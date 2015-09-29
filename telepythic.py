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
        """Return the response to the *IDN? query. To ensure you're communicating with the device you expect, specify an "expect" string which is matched against the start of the IDN response"""
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
		If the number of points is known in advance, it is checked
        
        Block data is of the form:
            #    - the ASCII character "#"
            N    - the size of following length string (single ASCII digit)
            M..M - number of bytes in the following data string (N-digits of ASCII)
            X..X - the actual data string
        """
        if not self.bstream:
        	data = self.read_raw(None)
        	head = data[:2]
        	assert head[0] == '#', 'Not a binary block array'
        	hlen = int(data[1])
        	dlen = int(data[2:2+hlen])
        	assert len(data) - (2+hlen+dlen) <= 2
        	data = data[2+hlen:2+hlen+dlen]
        else:
        	head = self.read_raw(2)
        	assert head[0] == '#', 'Not a binary block array'
        	dlen = int(self.read_raw(int(head[1])))
        	data = self.read_raw(dlen)
        if format is None:
        	return data
        return np.fromstring(data,dtype=format)
    
    def parse_reply(self, x):
        """Interpret the reply string and return an appropriately type-cast value"""
        try:    return int(x)
        except: pass
        try:    return float(x)
        except: pass
        if x[0] == '"': return x[1:x.rfind('"')]
        return x
    
    def ask(self, query, size=None):
        """A helper function that writes the command "query" and reads the reply. If "size" is not None, the response is assumed to be a binary string of that length."""
        self.dev.write(query)
        if size is None:
            return self.dev.read()
        else:
            return self.dev.read_raw(size)
    
    def query(self, query):
        """A helper function that asks "query" and returns the response.
        """
        if isinstance(query,str):
            return self.parse_reply(self.ask(query))
        else:
            return { q: self.query(q) for q in query }
    
    def read(self):
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
