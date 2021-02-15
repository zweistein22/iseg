import sys
import time
from os import path
import json
import toml


# Add import path for inplace usage
sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '../../..')))
# pylint: disable=wrong-import-position
from entangle.core import states
import CC2xlib.globals
import CC2xlib.json_data
import CC2xlib.CC2xjsonhandling
import CC2x
import isegCC2xChannel


operatingstyle = """
{
    "Control.currentSet" : 1.0,
    "Setup.delayedTripTime" : 500,
	"Setup.delayedTripAction" : 2
}
"""

jos = json.loads(operatingstyle)

for style in jos:
    print(style)
    v = jos[style]
    print(v)

respath = 'CC2xlib/example/Erwin-both.res'
#respath = 'CC2xlib/example/HV-TEST.res'

class PowerSupply(isegCC2xChannel.PowerSupply):
    _props = {}
    #log = logging.getLogger()
    # pylint: disable=unused-argument, super-init-not-called
    def __init__(self, logger=None):
        with open(respath) as fd:
            data = toml.load(fd)
            tango_name = 'test/Erwin/HV-Powersupply-Channel016'
            self.address = data[tango_name]['address']
            self.user = data[tango_name]['user']
            self.password = data[tango_name]['password']
            self.channel = data[tango_name]['channel']
            if 'operatingstyle' in data[tango_name]:
                self.operatingstyle = data[tango_name]['operatingstyle']
        self._state = (states.INIT,self.address)
        self.init()

class IntelligentPowerSupply(CC2x.IntelligentPowerSupply):

    _props = {}
    #log = logging.getLogger()
    # pylint: disable=unused-argument
    def __init__(self, logger=None):
        #super(CC2x.IntelligentPowerSupply, self).__init__(log)

        with open(respath) as fd:
            data = toml.load(fd)
            tango_name = 'test/Erwin/HV-IntelligentPowersupply'
            self.address = data[tango_name]['address']
            self.user = data[tango_name]['user']
            self.password = data[tango_name]['password']
            if 'transitions' in data[tango_name]:
                self.transitions = data[tango_name]['transitions']
            if 'groups' in data[tango_name]:
                self.groups = data[tango_name]['groups']
            if 'operatingstyles' in data[tango_name]:
                self.operatingstyles = data[tango_name]['operatingstyles']
            if 'tripeventallmodulesoff' in data[tango_name]:
                self.tripeventallmodulesoff = data[tango_name]['tripeventallmodulesoff']
        self._state = (states.INIT,self.address)
        self.init()




    def setGroupItemValues(self,groupname,cmditem,channelvalues):
        rol = []
        channels = self.jgroup[groupname]['CHANNEL']
        rampstyle = self.jgroup[groupname]['OPERATINGSTYLE']
        for rstyle in self.joperatingstates :
            stylename = list(rstyle.keys())[0]
            if stylename == rampstyle :
                # pylint: disable=redefined-outer-name
                for k, v in rstyle[stylename].items():
                    item = k
                    if len(channels) != len(channelvalues):
                        raise Exception('len list of channelvalues ', 'not equal len list of channels in group ' + groupname)
                    for channel in channels :
                        rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,item,v))
        j = 0
        for channel in channels :
            rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,cmditem,channelvalues[j]))
            j = j + 1
        return rol

a = IntelligentPowerSupply()
while True:
    time.sleep(1)
    st2 = a.state()
    if st2[0] != states.INIT:
        break


for i in range(0,25):
    time.sleep(1)
    print(a.state())

#b = PowerSupply()
#time.sleep(1)
#b.Off()
#time.sleep(1)
#b.On()
#time.sleep(1)
#for i in range(0,20):
#      z = b.state()
#      print(z)
#      time.sleep(1)
#      b.write_voltage(102.5)


n_items = a.read_availableLines()

delays = []
cmds = []

for i in range(n_items):
    delays.append(0)
    cmd = "TR" + str(i)
    cmds.append(cmd)

transitionnames = a.MultiCommunicate((delays,cmds))
cmd = 'APPLY:' + transitionnames[0]
a.Write(cmd)

for i in range(0,25):
    time.sleep(1)
    print(a.state())



while True:
    time.sleep(1)
    st = a.state()
    if st[0] != states.BUSY:
        break

print("here")
print(st)
statusjsonstr = a.read_jsonstatus()
#print(statusjsonstr)
a.Off()
time.sleep(3)
a.On()

while True:
    time.sleep(1)
    st = a._state

    st2 = a.state()
    if st[0] != states.INIT:
        break


a.Write(cmd)

for i in range(0,25):
    time.sleep(1)
    print(a.state())

#for i in range(0,7):
#    print("Cycle"+str(i))
#    time.sleep(1)
#    a.delete()
#    a = PowerSupply()

#print("END CYCLES")

#sys.exit()

#t = a.getTransitionNames()
#a.setVoltage(([29],['0_0_0']))

#a.applyTransition("goOn")
#for i in range(10):
#    time.sleep(1)

#statusjsonstr = a.read_jsonstatus()
#voltage004 = CC2xlib.CC2xjsonhandling.getStatusValue("0_0_4","Status.voltageMeasure",statusjsonstr)
#if voltage004:
#    print("\r\n"+"0_0_4"+ " : "+ "Status.voltageMeasure" +"="+ str(voltage004)+"\r\n")
#for i in range(15):
#   time.sleep(1)

#a.applyTransition("goOff")
