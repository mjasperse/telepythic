"""
TEKTRONIX OSCILLOSCOPE INTERFACE
Connects to TekTronix TDS, DPO and MSO oscilloscopes, and provides a simple interface to download data from the scope.

Programming guides: http://www.tek.com/search/apachesolr_search/programmer?filters=type%3A%28%22manual%22%29%20tid%3A1012
"""

from telepythic import TelepythicDevice
import numpy as np

class TekScope(TelepythicDevice):
    """Helper class for communicating with TekTronix digital oscilloscopes."""
    def __init__(self,interface,**kwargs):
        """Connect to scope over specified interface. If "interface" is string, connect as a telnet instance"""
        if isinstance(interface,str):
            from telepythic import TelnetInterface
            interface = TelnetInterface(
                host = interface,
                port = 4000,
                eom = b'\n',
                prompt = b'> ',
                **kwargs)
        TelepythicDevice.__init__(self,interface)
        # turn off verbose modes
        self.write(b'VERB 0; HEAD 0')
        
    def channels(self,all=True):
        """Return a dictionary of the channels supported by this scope and whether they are currently displayed.
        Includes REF and MATH channels if applicable. If "all" is False, only visible channels are returned"""
        # want to enable HEAD to get channel names as well
        prev = self.ask(b'HEAD?')
        self.write(b'HEAD 1')
        # determine the device capabilities and enabled status
        resp = self.ask(b'SEL?').rsplit(b':',1)[1]
        # reset HEAD
        self.write(b'HEAD '+prev)
        # create a dict from the response
        vals = {}
        for x in resp.split(b';'):
            name, val = x.rsplit(b' ',1)
            if name[0] == b':': name = name.rsplit(b':',1)[1]
            try:    visible = bool(int(val))
            except: continue
            if all or visible:
                vals[name] = visible
        return vals

    def waveform(self,channel=None,ascii_mode=False):
        """Downloads the active (or the specified) channel from the scope in binary mode (unless "ascii_mode" is True).
        Returns a tuple (A,T,Y) consisting of channel attributes as queried with WFMP? and 1D arrays of time and y-values"""
        # select channel if required
        if channel is not None:
            if isinstance(channel,int) or channel in b'1234':
                channel = b'CH'+str(channel)
            if not isinstance(channel,str):
                raise TypeError("Invalid type for channel")
            self.write(b'DAT:SOU '+channel.strip())
            # check that it worked
            try: self.ask(b'DAT:SOU?') # should timeout if it failed
            except: raise ValueError("Invalid channel")
			
        # configure output mode
        if ascii_mode:
            self.write(b'DAT:ENC ASCII')
        else:
            self.write(b'DAT:ENC RIB; WID 2')
        # want to enable HEAD for settings names
        prev = self.ask(b'HEAD?')
        self.write(b'HEAD 1')
        # create a dict of all the settings
        wfmo = self.ask(b'WFMP?')
        assert wfmo.startswith(b':WFMP'), 'Unknown response header'
        wfmo_vals = wfmo[wfmo.find(':',1)+1:].split(b';')
        
        def parse(x):
            try:    return int(x)
            except: pass
            try:    return float(x)
            except: pass
            if x[0] == b'"': return x[1:x.rfind(b'"')]
            return x
        
        wfmo = {}
        for x in wfmo_vals:
            name, val = x.split(b' ',1)
            wfmo[str(name)] = parse(val)
        npts = wfmo['NR_P']
        assert npts > 0
        
        self.write(b'HEAD 0')
        # flush anything waiting to be read
        self.flush()
        # get the raw curve data
        if ascii_mode:
            data = self.ask(b'CURV?')
            Y = np.fromstring(data,sep=b',')
        else:
            fmt = ('>' if wfmo['BYT_O'] == b'MSB' else '<') + 'i' + str(wfmo['BYT_N'])
            Y = self.ask_block(b'CURV?',format=fmt)
        assert len(Y) == npts, 'Incorrect response size'
        # transform the data
        T = wfmo['XIN']*np.arange(0,npts) + wfmo['XZE']
        Y = wfmo['YMU']*(Y - wfmo['YOF']) + wfmo['YZE']
        # reset HEAD
        self.write(b'HEAD '+prev)
        return wfmo, T, Y

    def lock(self,locked=True):
        """Lock (or unlock) the scope's front panel"""
        self.write(b'LOCK ALL' if locked else b'LOCK NONE')


if __name__ == '__main__':
    import _cmdline
    ifc = _cmdline.parse("Tektronix digital oscilloscopes",telnet=True,port=4000)
    dev = TekScope(ifc)
    import pylab as pyl
    for ch in dev.channels(True):
        wfmo, T, Y = dev.waveform(ch)
        pyl.plot(T,Y)
    pyl.show()
