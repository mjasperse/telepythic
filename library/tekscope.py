from telepythic import TelepythicDevice
import numpy as np

class TekScope(TelepythicDevice):
    def __init__(self,interface,**kwargs):
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
        
    def waveform(self,channel=None):
        # select channel if required
        if channel is not None:
            if isinstance(channel,int) or channel in '1234':
                channel = 'CH'+str(channel)
            self.write('DAT:SOU '+channel)
        # configure channel for output
        self.write('WFMP:ENC BINARY; BN_F RI; BYT_N 2')
        # create a dict of all the settings
        wfmo = self.ask('HEAD 1; WFMP?')
        assert wfmo.startswith(':WFMP:')
        wfmo_vals = wfmo[6:].split(';')
        
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
		
        # flush anything waiting to be read
        self.flush()
        # get the raw curve data
        self.write('HEAD 0')
        self.write('CURV?')
        Y = self.read_block(format=fmt)
        assert len(Y) == npts
        # transform the data
        T = wfmo['XIN']*np.arange(0,npts) + wfmo['XZE']
        Y = wfmo['YMU']*(Y - wfmo['YOF']) + wfmo['YZE']
        return wfmo, T, Y

    def lock(self,locked=True):
        self.write('LOCK ALL' if locked else 'LOCK NONE')
