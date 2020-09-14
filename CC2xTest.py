import sys
from os import path

# Add import path for inplace usage
sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '../../..')))


import toml
import json
from CC2xlib.globals import add_monitor, queue_request
from entangle.core import states 


class PowerSupply():

      def __init__(self, *args, **kwargs):
           #with open('../../../example/Erwin-small-HV.res') as fd:
           with open('CC2xlib/example/Erwin-small-HV.res') as fd:
               data = toml.load(fd)
               tango_name = "test/Erwin/HV-Powersupply"
               self.groups = data[tango_name]["groups"]
               self.operatingstyles = data[tango_name]["operatingstyles"]
               self.address = data[tango_name]["address"]
               self.user = data[tango_name]["user"]
               self.password = data[tango_name]["password"]

           return super().__init__(*args, **kwargs)

      def init(self):
          print("Init")
          self.jgroups = json.loads(self.groups)
          #checkchannels(groups)
          self.joperatingstyles = json.loads(self.operatingstyles)

          for group in self.jgroups:
              #groupname = list(group.keys())[0]
              print(group)

          #checkoperatingstates(operatingstates)
          add_monitor(self.address,self.user,self.password)
          self.state = states.ON
     
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
                            rol.append(json_data.make_requestobject("setItem",channel,item,v))
                    rol.append(setItemValue(channels,cmditem,channelvalues))
        return rol
        


      def rolAddOperatingStyle(self,groupname):
        rol = [] # request object list 
        channels = self.jgroup[groupname]['CHANNEL']
        rampstyle = self.jgroup[groupname]['OPERATINGSTYLE']
        for rstyle in self.joperatingstates :
            stylename = list(rstyle.keys())[0]
            if stylename == rampstyle :
                for k, v in rstyle[stylename].items():
                    item = k
                    for channel in channels :
                        rol.append(json_data.make_requestobject("setItem",channel,item,v))
        return rol
      
      def getChannels(self,groupname):
           return self.jgroup[groupname]['CHANNEL']
           
      def rolSetVoltage(self, arg):
          if len(arg) != 2 :
               raise Exception('SetVoltage(arg)', 'is not a pair of objects (must be lists)')
          keys = arg[1]
          values = arg[0]
          # check channel is one of groups
          if len(keys) != len(values) :
               raise Exception('len list of values ', 'not equal len list of keys')

          rol = []

          for i in range(len(keys)):
             rol.append(setItemValue(self,keys[i],"Control.setVoltage",values[i]))
     
          return rol
      def ApplyTransition(self,transition):
        pass
     
   


a = PowerSupply()

a.init()

channels = a.getChannels("Anodes")

rol = a.rolSetVoltage(([3.0],["0_0_0"]))
queue_request(rol)


