# Telepythic #

This library is for communicating with measurement and test-equipment using text-based VISA (e.g. GPIB-like) interfaces. It's intended purpose is to simplify writing scripts to control equipment and download measurements, in an interface-agnostic way.

Classes are provided for TCP communication (e.g. Tektronix oscilloscopes), and GPIB communication via a Prologix ethernet-GPIB bridge. Direct interface with VISA drivers is possible through the pyvisa project. The simple read/write/ask interface means devices do not need to know the details of the underlying interface, meaning interfaces can be easily changed.

Telepythic takes care of end-of-message, end-of-input, and buffering considerations, to provide a reliable and simple means of communication.

This example shows how to download an entire trace from an HP4395 vector-network analyser, using an ethernet-GPIB interface, in binary mode, taking less than a second:


```
#!python

# connect to a prologix GPIB bridge
bridge = PrologixInterface(gpib=17,host=175)
# create a generic device instance
dev = TelepythicDevice(bridge)
# make sure the device is connect and identifies correctly
id = dev.id(expect="HEWLETT-PACKARD,4395A")
# download spectrum in 64-bit mode
dev.send('FORM3; OUTPDTRC?')
spec = dev.read_block('f8')
```

More detailed examples are available in the library/ directory.


### How do I use it? ###

The library can either be used by instantiating a TelepythicDevice and using it directly in a script (e.g. library/sr770.py), or by creating a subclass (e.g. library/tekscope.py).

The constructor takes an interface object, which is any class that provides the following functions:
* write(data), write the binary string "data" to the device
* read(), read an ASCII response string from the device
* read_raw(size), read exactly "size" bytes back from the device

This simple interface is compatible with other driver projects, such as pyvisa.