"""
TELEPYTHIC -- a python interface to test equipment
Copyright 2014 by Martijn Jasperse
https://bitbucket.org/martijnj/telepythic
"""
import numpy as np

class TelepythicError(Exception):
    """A simple exception class for use with telepythic, that wraps underlying protocol errors."""
    def __init__(self,device,base,descr=None):
        if base is not None:
            # are we daisy-chaining wrapper classes?
            if hasattr(base, 'base_error'):
                base = base.base_error
            # append the description from the base error
            if descr is None:
                descr = str(base)
            else:
                descr = descr + ': ' + str(base)
        # initialise the standard exception class
        super(Exception,self).__init__(descr.format(device=str(device)))
        # store variables
        self.device = device
        self.base_error = base

class ConnectionError(TelepythicError):
    """An error occurred while attempting to connect to the device"""
    def __init__(self,device,base,reason=None):
        descr = 'Failed to connect to {device}'
        if reason is not None: descr = descr + ': ' + reason
        TelepythicError.__init__(self,device,base,descr)

class QueryError(TelepythicError):
    """A helper class that describes the command which failed and why"""
    def __init__(self,device,base,query):
        TelepythicError.__init__(self,device,base,'Query '+repr(query)+' on {device} failed')
        self.query = query


class TelepythicDevice:
    def __init__(self,interface):
        """
        Create a device instance using the provided interface.
        
        The interface can be any class that provides the following functions:
            read(), read_raw(), write()
        """
        self.dev = interface
        # do we have an underlying bytestream that can be read in segments? (not supported by VISA)
        # see also read_block()
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
                raise TelepythicError(self.dev,None,'Expected ID '+repr(expect)+', got '+repr(id))
        return id
    
    def read_block(self,format=None):
        """Read a GPIB-style block of binary data from the device. If "format" is specified, the data is reinterpreted as a 1D numpy array with the corresponding dtype.
        
        GPIB block data is a binary stream of the form:
            #    - the ASCII character "#"
            N    - the size of following length string (single ASCII digit)
            M..M - number of bytes in the following data string (N-digits of ASCII)
            X..X - the actual data string (M bytes of binary data)
        
        NB: Be sure to specify include the endian specification in the format string! (e.g. ">f8" for 64-bit big-endian data)
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
        # is it anything at all?
        if not len(x): return None
        # is it an integer?
        try:    return int(x)
        except: pass
        # is it a floating point value?
        try:    return float(x)
        except: pass
        # is it a string?
        if x[0] == '"': return x[1:x.rfind('"')]
        return x
    
    def ask(self, query, size=None):
        """A helper function that writes the command "query" and reads the reply. If "size" is not None, the response is assumed to be a binary string of that length"""
        try:
            self.dev.write(query)
            if size is None:
                return self.dev.read()
            else:
                return self.dev.read_raw(size)
        except Exception as e:
            raise QueryError(self.dev, e, query)
    
    def ask_block(self, query, format=None):
        """A helper function to ask a query that returns a GPIB "block" format response. See also read_block()"""
        try:
            self.dev.write(query)
            return self.read_block(format)
        except Exception as e:
            raise QueryError(self.dev, e, query)
    
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
        try:
            return self.dev.read()
        except Exception as e:
            raise TelepythicError(self.dev, e)
    
    def read_raw(self, size):
        """Read exactly "size" bytes from the device"""
        try:
            return self.dev.read_raw(size)
        except Exception as e:
            raise TelepythicError(self.dev, e)
    
    def write(self, msg):
        """Write the specified string to the device"""
        try:
            return self.dev.write(msg)
        except Exception as e:
            raise TelepythicError(self.dev, e)
    
    def flush(self):
        """Removes any pending response, returning the number of bytes flushed, or -1 if not supported by the device"""
        if hasattr(self.dev,"flush"):
            try:
                return self.dev.flush()
            except Exception as e:
                raise TelepythicError(self.dev, e)
        return -1
    
    def close(self):
        """Close the connection to the associated device. Unlocks the device if the relevant command exists."""
        if hasattr(self,"lock"):
            self.lock(False)
        elif hasattr(self.dev,"lock"):
            self.dev.lock(False)
        self.dev = None


def find_visa(resource,timeout=1):
    """Use pyvisa to connect to a VISA resource described by "resource", which may contain wildcards.
    The VISA communications timeout is "timeout", specified in seconds."""
    try:    import pyvisa
    except: raise ImportError('Requires "pyvisa" to use VISA resources')
    try:
        # query all available VISA devices
        rm = pyvisa.ResourceManager()
        # enumerate the USB devices
        devs = rm.list_resources(resource)
        # check there's only one
        assert len(devs) != 0, "No VISA resource found"
        assert len(devs) < 2, "Resource describes %i devices"%len(devs)
        # open the device
        instr = rm.open_resource(devs[0])
        instr.timeout = timeout*1000 # VISA timeout in ms
    except Exception as e:
	    raise ConnectionError(repr(resource),e)
    return instr

def pyvisa_connect(resource,timeout=1):
    """Legacy name for find_visa()"""
    return find_visa(resource,timeout)
