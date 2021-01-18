# iseg HV module

this software is an interface to the [entangle framework](
https://forge.frm2.tum.de/entangle/doc/entangle-master/build/)
for high-voltage modules of the CCR series from the company [Iseg spezialelektronik Gmbh](https://iseg-hv.com/en/home)

A standalone example in python is also supplied (CC2xTest.py).

The core of the module is an async web socket connection to the iseq CCR module running in a separate thread. Incoming and outgoing messages are then converted back and forth from the correct format needed by the entangle framework.

Hardlimits.py can be edited to change maximum settings for Voltage and TripCurrent.





