from telepythic import TelepythicDevice, TelnetInterface

class TekScope(TelepythicDevice):
    def __init__(self,interface,**kwargs):
        if isinstance(interface,str):
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
			if isinstance(channel,int): channel = 'CH%i'%channel
			self.write('DAT:SOU '+channel)
        # configure channel for output
        self.write('WFMO:ENC BINARY; BN_F RI; BYT_N 2; BYT_O LSB')
        # create a dict of all the settings
        wfmo = self.ask('WFMO?')
        wfmo_keys = [
            'BYT_NR',   # data width for the outgoing waveform
            'BIT_NR',   # bits per data point
            'ENCDG',    # encoding (ASCII or binary)
            'BN_FMT',   # signed-ness of binary data
            'BYT_OR',   # endian-ness (LSB or MSB first)
            'WFID',     # acquisition parameters 
            'NR_PT',    # number of points
            'PT_FMT',   # point format: {ENV: min/max pairs, Y: single points}
            'XUNIT',    # horizontal units
            'XINCR',    # horizontal increment
            'XZERO',    # time of the first point
            'PT_OFF',   # is currently displayed?
            'YUNIT',    # vertical units
            'YMULT',    # vertical scale factor per digitizing level
            'YOFF',     # vertical position in digitizing levels
            'YZERO'     # vertical offset
        ]
        def parse(x):
            try:    return int(x)
            except: pass
            try:    return float(x)
            except: pass
            if x[0] == '"': return x[1:x.rfind('"')]
            return x
        wfmo_vals = map(parse, wfmo.split(';'))
        wfmo = dict(zip(wfmo_keys,wfmo_vals))
        npts = wfmo['NR_PT']
        assert npts > 0
        # flush anything waiting to be read
        self.flush()
        # get the raw curve data
        data = self.write('CURV?')
        Y = self.read_block(format='<i2')
        # transform the data
        T = wfmo['XINCR']*np.arange(0,npts) + wfmo['XZERO']
        Y = wfmo['YMULT']*(Y - wfmo['YOFF']) + wfmo['YZERO']
        return wfmo, T, Y

    def lock(self,locked=True):
        self.write('LOCK ALL' if locked else 'LOCK NONE')
