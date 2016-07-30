"""
TELEPYTHIC -- a python interface to test equipment
Copyright 2014 by Martijn Jasperse
https://bitbucket.org/martijnj/telepythic
"""
import argparse
import telepythic

def process_args(name,tcp_only=False,output=True,port=None):
	opt = argparse.ArgumentParser(description = "Python interface to "+name)
	opt.add_argument('-i','--host','--ip',metavar='ADDR',type=str,help='connect to device with specified IP address',required=tcp_only)
	opt.add_argument('-p','--port',metavar='PORT',type=int,help='port for TCP connection',default=port)
	if not tcp_only:
		opt.add_argument('-g','--gpib',metavar='ADDR',type=int,help='connect to device at this GPIB address')
		opt.add_argument('-V','--visa',metavar='RES',type=str,help='connect to this VISA resource')
		opt.epilog = "TCP interface is used by default, but if both GPIB and TCP are set then the Prologix interface will be used instead. Note that if VISA is specified, the other connection parameters are ignored."
	opt.add_argument('-t','--timeout',metavar='T',type=int,help='timeout for communication',default=1)
	opt.add_argument('-o','--output',metavar='F',help='save collected data to specified file')
	args = vars(opt.parse_args())
	
	# drop the None values
	args = {k:v for k,v in args.items() if v is not None}
	if not ('host' in args or 'gpib' in args or 'visa' in args):
		opt.error('Inadequate interface information specified')
	if 'host' in args and not ('port' in args or 'gpib' in args):
		opt.error('TCP port must be specified')
	return args

def parse(name,telnet=False,*args,**kwargs):
	if telnet: kwargs['tcp_only'] = True
	args = process_args(name,*args,**kwargs)
	f = args.pop('output',None)
	if 'visa' in args:
		# VISA connection
		return telepythic.find_visa(args['visa'],args['timeout'])
	elif 'host' in args:
		if 'gpib' in args:
			# prologix interface
			return telepythic.PrologixInterface(**args)
		elif telnet:
			# telnet connection
			return telepythic.TelnetInterface(**args)
		else:
			# raw TCP connection
			return telepythic.TCPInterface(**args)
	elif 'gpib' in args:
		# probably a VISA connection
		return telepythic.find_visa('GPIB0::%d::INSTR'%args['gpib'])
	raise NotImplementedError("Unknown connection specified")

if __name__ == '__main__':
	print parse("Test device")
