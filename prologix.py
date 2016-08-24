"""
TELEPYTHIC -- a python interface to test equipment
Copyright 2014 by Martijn Jasperse
https://bitbucket.org/martijnj/telepythic
"""
from tcp import TCPInterface
from telepythic import TelepythicError, ConnectionError

class PrologixInterface(TCPInterface):
    _protocol = 'Prologix'
    def __init__(self, gpib, host, port=1234, timeout=1, auto=True, assert_eoi=True, eos=None, poll=True):
        """
        Connect to the Prologix Ethernet<->GPIB bridge at (host,port) and communicate with the device at the specified GPIB address. Attempts to poll the device after connection to ensure device is operating.
        
        The Prologix writes its buffer to the GPIB address upon receiving '\\n' (automatically appended if not present). This '\\n' is removed and replaced with the "eos" string, and the EOI line is optionally asserted.
        
        Keyword arguments:
        auto        -- automatically read after every write command, as opposed to issuing "++read" on every read command (default: True)
        assert_eoi  -- assert the EOI GPIB line with the last character sent (default: True)
        eos         -- string to append to signify End-Of-Send, must be one of '\\n', '\\r' or '\\r\\n' (default None)
        """
        # connect to prologix unit (prologix itself requires '\n' eom termination)
        TCPInterface.__init__(self,host,port,timeout,eom='\n')
        # make sure it's what we expect
        self.write('++ver\n')
        if not self.read(True).startswith('Prologix GPIB'):
            raise ConnectionError(self,None,'Not a Prologix device')
        
        # set controller mode
        self.write('++mode 1\n')
        # set timeout for reading gpib response (in ms)
        self.write('++read_tmo_ms %i\n'%int(timeout*1000))
        # set gpib address of device to connect to
        self.write('++addr %i\n'%gpib)
        # assert eoi with every write?
        self.write('++eoi %i\n'%assert_eoi)
        # what kind of eos to append?
        if eos is None or eos == '':    eos = 3
        elif eos == '\n':               eos = 2
        elif eos == '\r':               eos = 1
        elif eos == '\r\n':             eos = 0
        elif not eos in (0,1,2,3):      raise ValueError('Unknown EOS mode')
        self.write('++eos %i\n'%eos)
        # attempt to read after every write?
        self.write('++auto %i\n'%auto)
        self.auto = auto
        
        # can we serial poll the device?
        if poll:
            try:    self.poll()
            except: raise ConnectionError(self,None,'Device did not respond to poll')
        
    def __del__(self):
        # clean up if possible
        try:    self.close()
        except: pass
        
    def read(self,immediate=False):
        """
        Read data from the Prologix unit.
        If the device was not configured in "auto" mode (see __init__), a "++read" command is issued.
        To read a response to a Prologix query (starting with "++"), set immediate to True.
        """
        # if we're not in auto mode, need to tell prologix to read
        if not immediate and not self.auto: self.write('++read eoi\n')
        # pull from tcp
        return TCPInterface.read(self)
    
    def clear(self):            self.write('++clr\n')
    def lock(self,locked=True): self.write('++llo\n' if locked else '++loc\n')
    def local(self):            self.write('++loc\n')
    def reset(self):            self.write('++rst\n')
    def poll(self):             self.write('++spoll\n'); return int(self.read(True))
    def srq(self):              self.write('++seq\n'); return int(self.read(True))

