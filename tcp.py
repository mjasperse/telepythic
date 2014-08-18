import socket, select
class TCPInterface:
    def __init__(self, host, port, timeout=1, eom='\r\n', trim=True, buffer=1024):
        """
        Connect to the specified TCP device
        
        Keyword arguments:
        host    -- Host name or IP address of device to connect to
        port    -- Port to connect to on host
        timeout -- Communication timeout, in seconds (default: 1)
        eom     -- "End-Of-Message" string, appended to outgoing messages if not present (default: \r\n)
        trim    -- Whether to trip whitespace from responses (default: True)
        buffer  -- TCP receive buffer chunk size (default: 1024)
        """
        if isinstance(host,int):
            assert host >= 0 and host < 256
            # get the local (default) ip address -- probably breaks on multiple interface machines
            myaddr = socket.gethostbyname_ex('')[2][0]
            # replace the last octet
            host = myaddr.rsplit('.',1)[1] + str(host)
        # create a TCP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.sock.settimeout(timeout)
        # connect to host
        try:
            self.sock.connect((host, port))
        except socket.timeout:
            raise socket.timeout('Failed to connect to %s:%i'%(host,port))
        self.eom = eom
        self.trim = trim
        self.buffer = buffer
        self.host = host
    
    def close(self):
        """Close the associated socket"""
        self.sock.close()
    
    def has_reply(self,timeout=0):
        """Checks whether a reply is waiting to be read"""
        # is something waiting on the socket to be read?
        socklist = select.select([self.sock],[],[],timeout)
        return len(socklist[0])>0
    
    def flush(self,timeout=0):
        """Removes any pending data to be received from the socket, and returns the number of bytes flushed"""
        # read with zero timeout until there's nothing remaining to read
        n = 0
        while self.has_reply(timeout):
            n += len(self.sock.recv(self.buffer))
        return n
        
    def read(self):
        """Read data from the socket, trim the whitespace if specified in the constructor"""
        # pull all the data off the line
        data = self.sock.recv(self.buffer)
        while self.has_reply(timeout=0):
            data += self.sock.recv(self.buffer)
        if self.trim:
            return data.trim()
        return data
    
    def read_raw(self,size):
        """Reads exactly "size" bytes from the socket"""
        # read exactly size bytes from the input
        data = self.sock.recv(size)
        while size > len(data):
            data += self.sock.recv(size-len(data))
        return data
    
    def write(self,msg):
        """Sends the "msg" string to the socket, appending the End-Of-Message (eom) string if not present. Returns the number of bytes sent"""
        # append eom if not already there
        if self.eom is not None and not msg.endswith(self.eom):
            msg += self.eom
        self.sock.send(msg)
        # return bytes sent
        return len(msg)
    
import re
class TelnetInterface:
    def __init__(self, host, port, timeout=1, eom='\n', prompt='> '):
        """
        Create a Telnet-style connection to the specified device. Telnet connections are TCP connections where the device emits a ready-for-input string ("prompt") that needs to be removed from responses.
        
        Keyword arguments are per TCPInterface
        """
        TCPInterface.__init__(self,host,port,timeout=timeout,eom=eom,trim=False)
        # compile a regex that looks for any number of prompt strings
        self.prompt = prompt
        self.rex = re.compile('([\r\n ]*%s)+'%prompt)
        # wait for the ready prompt
        try:
            while re.search(prompt+'$', self.sock.recv(self.buffer)) is None:
                pass
        except socket.timeout:
            raise RuntimeError('Device did not return a ready prompt')

    def read(self):
        """Read data from the socket, until the ready-for-input prompt is received. The prompt string is removed from the response."""
        data = ''
        # read until we get something other than a prompt statement
        while len(data) == 0:
            data = TCPInterface.read(self)
            M = self.rex.match(data)
            if M is not None: data = data[M.end()+1:]
        # we have something, drop the prompt if it ends with one
        if data.endswith(self.prompt): data = data[:-len(self.prompt)].rstrip()
        return data
        
    def flush(self,timeout=0.25):
        """Flush any data waiting to be read (default timeout 250ms)"""
        return TCPInterface.flush(self,timeout)

