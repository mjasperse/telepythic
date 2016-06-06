# Telepythic #

This library is for communicating with measurement and test-equipment using text-based VISA (e.g. GPIB-like) or telnet interfaces. Its intended purpose is to simplify writing scripts to control equipment and download measurements, in an interface-agnostic way.

Ready-to-use classes are provided for communicating directly through TCP over ethernet, GPIB through VISA (requires [pyvisa], see below) or an ethernet-GPIB bridge (such as the [Prologix] bridge).

The simple read/write/ask interface means devices do not need to know the details of the underlying interface, meaning interfaces can be easily changed.
**Telepythic takes care of end-of-message, end-of-input, and buffering considerations**, providing a simple and reliable means of communication.
It handles both binary transfer and delimited text, allowing for both human-readable communication and efficient data transfer.

The following example shows how to download an entire trace from an HP4395 vector-network analyser (VNA) in binary mode over an ethernet-GPIB interface, producing a `numpy` array of the data in less than a second:
```python
# connect to a prologix GPIB bridge
bridge = PrologixInterface(gpib=17,host=175)
# create a generic device instance
dev = TelepythicDevice(bridge)
# make sure the device is connect and identifies correctly
id = dev.id(expect="HEWLETT-PACKARD,4395A")
# change to 64-bit binary mode and download spectrum
dev.write('FORM3; OUTPDTRC?')
spec = dev.read_block('f8')
```

Several examples [are provided in the `library/` directory][library] showing how to interface with different types of device:
* Agilent 86140B Optical Spectrum Analyser
* Ando AQ6315 Optical Spectrum Analyser
* Galil RIO Programmable Logic Controller
* HP 4395A Vector Network Analyser
* Stanford SR770 FFT Network Analyser
* TekTronix Digital Oscilloscopes

   
### How do I use it? ###

The library uses two kinds of classes: **interfaces** and **devices**.
First you create an instance of the interface you want to communicate with (e.g. TCP or VISA), and then create a device that uses that interface.
You can either create an instance of `TelepythicDevice` directly, or subclass it to provide convenience functionality (e.g. [the TekScope class][tekscope], which enables direct download of displayed waveforms).

The "interface" is any class that provides the following functions:
* `write(data)`, write the binary string "data" to the device
* `read()`, read an ASCII response string from the device
* `read_raw(size)`, read exactly "size" bytes back from the device

This simple definition is compatible with other driver projects, such as [pyvisa][pyvisa] (see below).

The classes provided by `telepythic` account for several problems that naive handlers may fail at, for example a TCP connection where a response is split over many packets, EOL appearing in binary transfers, and EOM in Telnet sessions.

Although you can communicate directly using the interface class, it is recommended to use the separate "device" class so that the same code can be executed trivially on different interfaces, for example
```python
import telepythic
# define the interface
if tcp:
    # a direct TCP connection
	instr = telepythic.TCPInterface(ipaddress)
elif usb:
    # connect to USB using pyvisa
    instr = telepythic.pyvisa_connect('USB?*::INSTR')
# define the device
dev = telepythic.TelepythicDevice(instr)
```

The device class provides access to "write" and "read" commands, as well as a number of convenience functions:
* `id()` to send the standard query `*IDN?`, and optionally compare it against an expected reply.
* `read_block()` to interpret the binary "block" format of GPIB
* `ask()` for the combination of write-then-read.
* `query()` which behaves like `ask()`, but parses responses into python datatypes, and can construct a `dict` from a list of queries.



### Can I use VISA? ###

**Absolutely!** The excellent [pyvisa] module can be easily used as a back-end driver for `telepythic` to enable connection to any VISA-enabled device.
The wrapper function `pyvisa_connect` is provided to simplify connecting to a single device based on its VISA identification string (wildcards _are_ permitted).

For example, if there is only one USB instrument connected to the machine, connecting is as simple as
```python
import telepythic
instr = telepythic.pyvisa_connect('USB?*::INSTR')
dev = telepythic.TelepythicDevice(instr)
print dev.id()
```
Note that if multiple USB instruments are connected, a more specific VISA string should be used (e.g. including manufacturer/model number).
Otherwise the `pyvisa` resource manager should be used to iterate over the possible devices to find the one that you're after.

[pyvisa]: http://pyvisa.readthedocs.io/
[prologix]: http://prologix.biz/gpib-ethernet-controller.html
[library]: https://bitbucket.org/martijnj/telepythic/src/default/library/
[tekscope]: https://bitbucket.org/martijnj/telepythic/src/default/library/tekscope.py