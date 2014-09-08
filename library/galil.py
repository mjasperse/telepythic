from telepythic import TelepythicDevice, TelnetInterface
from struct import unpack
import re

# http://www.galilmc.com/support/manuals/com47xxx/index.html
# http://www.galilmc.com/support/manuals/man47100.pdf

class GalilRIO(TelepythicDevice):
    def __init__(self,interface,**kwargs):
        if isinstance(interface,str):
            interface = TelnetInterface(
                host = interface,
                eom = '\r\n',       # carriage return with newline
                prompt = [':','?'], # ":" denotes success, "?" denotes failure
                initial = 'EO 0',   # turn echo off on connection
                **kwargs)
        TelepythicDevice.__init__(self,interface)
        
    def query_error(self):
        """
        Query the error register for the last error code.
        Calling this function does not reset the register.
        """
        return int(float(self.ask('MG_TC')))
        
    def get_error(self):
        """
        Query the last error code and get a description.
        Note that making this call resets the error register
        """
        resp = self.ask('TC1').strip().split(' ',1)
        code = int(resp[0])
        if code == 0: return None
        return (code,resp[1])
        
    def get_record(self):
        """
        Query the data record from the Galil unit.
        Returns a dictionary of query results. Analog values are returned as integers, which map to voltages based on the AQ/DQ settings.
        """
        hdr = self.ask('QR',size=4)
        hdr, size = unpack('<HH',hdr)
        assert size == 56, 'Unexpected packet size'
        data = self.read_raw(size=size-4)
        sampl, err, status = unpack('<HBB',data[:4])
        ao = unpack('<HHHHHHHH',data[4:20])
        ai = unpack('<HHHHHHHH',data[20:36])
        do, di = unpack('<HH',data[36:40])
        do = [ bool((do>>i)&1) for i in range(16) ]
        di = [ bool((di>>i)&1) for i in range(16) ]
        pc, zc, zd = unpack('<Iii',data[40:52])
        return {
            'Header': hdr,
            'Sample': sampl,
            'Error': err,
            'Status': status,
            'Running': bool(status & 128),
            'Waiting': bool(status & 4),
            'Trace': bool(status & 2),
            'Echo' : bool(status & 1),
            'AO': ao,   # analog outputs (integer scaled)
            'AI': ai,   # analog inputs
            'DO': do,   # digital outputs (array of bools)
            'DI': di,   # digital inputs
            'PC': pc,   # pulse counter
            'ZC': zc,   # user variable C
            'ZD': zd    # user variable D
        }
    
    def get_handles(self):
        """
        Query the device's ethernet handles and return a dictionary of tuples with entries as follows:
            "self" = (IP address, MAC address)
            "A","B","C" = (remote IP, remote port, protocol (TCP or UDP), local port)
        If the handle is not connected, it does not appear in the dictionary.
        """
        data = self.ask('TH').split('\r\n')
        M = re.match('CONTROLLER IP ADDRESS ([\d,]+) ETHERNET ADDRESS (\w{2}-\w{2}-\w{2}-\w{2}-\w{2}-\w{2})',data[0])
        assert M is not None, 'Unknown response to TH'
        ip, mac = M.groups()
        handles = {'self': (ip.replace(',','.'), mac)}
        for l in data[1:]:
            M = re.match('IH([A-Z]) ([A-Z]+) PORT (\d+) TO IP ADDRESS ([\d,]+) PORT (\d+)',l)
            if M is None: continue
            hndl, proto, local, ip, remote = M.groups()
            handles[hndl] = (ip.replace(',','.'), int(remote), proto, int(local))
        return handles

    def get_program(self,split=False):
        """
        Instruct unit to upload its program to the connected host. If "split" is True, newlines are split for readability of compacted programs.
        """
        self.write('UL')
        data = ''
        while not data.endswith('\x1a'):    # terminates with Ctrl+Z
            data += self.read()
        data = data[:-1].strip()
        if split:
            data = data.replace(';','\n')
        return data
        