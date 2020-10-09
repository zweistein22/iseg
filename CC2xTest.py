import sys
import logging
import time
from os import path
import toml
# Add import path for inplace usage
sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '../../..')))
from entangle.core import states
import CC2xlib.globals
import CC2xlib.json_data
import CC2xlib.CC2xjsonhandling
import CC2x







class PowerSupply(CC2x.IntelligentPowerSupply):

    _props = {}
    #log = logging.getLogger()
    def __init__(self,logger=None):
        #super(CC2x.IntelligentPowerSupply, self).__init__(log)
        self.state = states.INIT
        with open('CC2xlib/example/Erwin-small-HV.res') as fd:
            data = toml.load(fd)
            tango_name = 'test/Erwin/HV-Powersupply'
            self.address = data[tango_name]['address']
            self.user = data[tango_name]['user']
            self.password = data[tango_name]['password']
            if 'transitions' in data[tango_name]:
                self.transitions = data[tango_name]['transitions']
            if 'groups' in data[tango_name]:
                self.groups = data[tango_name]['groups']
            if 'operatingstyles' in data[tango_name]:
                self.operatingstyles = data[tango_name]['operatingstyles']
            self.unitTime =  data[tango_name]['unitTime']
            self.unitCurrent = data[tango_name]['unitCurrent']
            self.maxTripCurrent = data[tango_name]['maxTripCurrent']
            self.maxVoltage = data[tango_name]['maxVoltage']
        self.init()




    def setGroupItemValues(self,groupname,cmditem,channelvalues):
        rol = []
        channels = self.jgroup[groupname]['CHANNEL']
        rampstyle = self.jgroup[groupname]['OPERATINGSTYLE']
        for rstyle in self.joperatingstates :
            stylename = list(rstyle.keys())[0]
            if stylename == rampstyle :
                for k, v in rstyle[stylename].items():
                    item = k
                    if len(channels) != len(channelvalues):
                        raise Exception('len list of channelvalues ', 'not equal len list of channels in group '+groupname)
                    for channel in channels :
                        rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,item,v))
        j = 0
        for channel in channels :
            rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,cmditem,channelvalues[j]))
            j = j + 1
        return rol





a = PowerSupply()

n_items = a.read_availableLines()

delays = []
cmds =[]

for i in range(n_items):
    delays.append(0)
    cmd = "TR" + str(i)
    cmds.append(cmd)

transitionnames = a.MultiCommunicate((delays,cmds))
cmd = 'APPLY:' + transitionnames[0]
a.Write(cmd)
time.sleep(5)

#a.Off()

time.sleep(10)

for i in range(0,7):
    print("Cycle"+str(i))
    time.sleep(1)
    a.delete()
    a = PowerSupply()

print("END CYCLES")

sys.exit()

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
