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
                eom = '\n',
                prompt = '> ',
                **kwargs)
        TelepythicDevice.__init__(self,interface)
        # turn off verbose modes
        self.write('VERB 0; HEAD 0')
        
    def channels(self):
        """Return a dictionary of the channels supported by this scope and whether they are currently displayed.
        Includes REF and MATH channels if applicable"""
        # want to enable HEAD to get channel names as well
        prev = self.ask('HEAD?')
        self.write('HEAD 1')
        # determine the device capabilities and enabled status
        resp = self.ask('SEL?').rsplit(':',1)[1]
        # reset HEAD
        self.write('HEAD '+prev)
        # create a dict from the response
        vals = {}
        for x in resp.split(';'):
            name, val = x.rsplit(' ',1)
            if name[0] == ':': name = name.rsplit(':',1)[1]
            try:    vals[name] = bool(int(val))
            except: continue
        return vals

    def waveform(self,channel=None):
        """Downloads the active (or the specified) channel from the scope in binary mode.
        Returns a tuple (A,T,Y) consisting of channel attributes as queried with WFMP? and 1D arrays of time and y-values"""
        # select channel if required
        if channel is not None:
            if isinstance(channel,int) or channel in '1234':
                channel = 'CH'+str(channel)
            self.write('DAT:SOU '+channel)
        # configure channel for output
        self.write('DAT:ENC RIB; WID 2')
        # want to enable HEAD for settings names
        prev = self.ask('HEAD?')
        self.write('HEAD 1')
        # create a dict of all the settings
        wfmo = self.ask('WFMP?')
        assert wfmo.startswith(':WFMP'), 'Unknown response header'
        wfmo_vals = wfmo.rsplit(':',1)[1].split(';')
        
        def parse(x):
            try:    return int(x)
            except: pass
            try:    return float(x)
            except: pass
            if x[0] == '"': return x[1:x.rfind('"')]
            return x
        
        wfmo = {}
        for x in wfmo_vals:
            name, val = x.split(' ',1)
            wfmo[name] = parse(val)
        fmt = ('>' if wfmo['BYT_O'] == 'MSB' else '<') + 'i' + str(wfmo['BYT_N'])
        npts = wfmo['NR_P']
        assert npts > 0
        
        self.write('HEAD 0')
        # flush anything waiting to be read
        self.flush()
        # get the raw curve data
        Y = self.ask_block('CURV?',format=fmt)
        assert len(Y) == npts, 'Incorrect response size'
        # transform the data
        T = wfmo['XIN']*np.arange(0,npts) + wfmo['XZE']
        Y = wfmo['YMU']*(Y - wfmo['YOF']) + wfmo['YZE']
        # reset HEAD
        self.write('HEAD '+prev)
        return wfmo, T, Y

    def lock(self,locked=True):
        """Lock (or unlock) the scope's front panel"""
        self.write('LOCK ALL' if locked else 'LOCK NONE')


if __name__ == '__main__':
    import _cmdline
    ifc = _cmdline.parse("Tektronix digital oscilloscopes",telnet=True,port=4000)
    dev = TekScope(ifc)
    import pylab as pyl
    for ch in dev.channels():
        wfmo, T, Y = dev.waveform(ch)
        pyl.plot(T,Y)
    pyl.show()
