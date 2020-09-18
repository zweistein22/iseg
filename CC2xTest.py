import sys
import time
from os import path
import toml
import json
# Add import path for inplace usage
sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '../../..')))
import CC2xlib.globals
import CC2xlib.json_data

import threading

from entangle.core import states 


class PowerSupply():

    def __init__(self, *args, **kwargs):
        self.state = 'INIT'
    #with open('../../../example/Erwin-small-HV.res') as fd:
        with open('CC2xlib/example/Erwin-small-HV.res') as fd:
            data = toml.load(fd)
            tango_name = "test/Erwin/HV-Powersupply"
            self.transitions = data[tango_name]["transitions"]
            self.groups = data[tango_name]["groups"]
            self.operatingstyles = data[tango_name]["operatingstyles"]
            self.address = data[tango_name]["address"]
            self.user = data[tango_name]["user"]
            self.password = data[tango_name]["password"]
        super().__init__(*args, **kwargs)

    def init(self):
        self.jtransitions = json.loads(self.transitions)
        self.jgroups = json.loads(self.groups)
        self.joperatingstyles = json.loads(self.operatingstyles)
        #checkoperatingstates(operatingstates)
        self.channels_handled = self.checkchannels()
        self.waitstring =''
        self.tw = None
        # access from other threads, so do the proper locking:
        # self.channels_handled
        # self.waitstring


        CC2xlib.globals.lock.acquire()
        CC2xlib.globals.instances.append(self)
        CC2xlib.globals.lock.release()
        CC2xlib.globals.add_monitor(self.address,self.user,self.password)

    def delete(self):
        CC2xlib.globals.lock.acquire()
        for i in CC2xlib.globals.instances:
            if i == self :
                CC2xlib.globals.instances.remove(i)
        CC2xlib.globals.lock.release()

    def __delete__(self):
        self.ApplyTransition("On>Off")
        
    def checkchannels(self):
        rv = []
        groups = self.jgroups['GROUP']
        for group in groups:
            for groupname in group:
                channels = self.getChannels(groupname)
                for ch in channels:
                    if ch in rv:
                        raise Exception("Duplicate channel '"+ch + "' in 'GROUP':"+group)

                    isusedbyother = False;
                    CC2xlib.globals.lock.acquire()
                    for i in CC2xlib.globals.instances:
                        if i != self:
                            if ch in i.channels_handled:
                                isusedbyother = True

                    CC2xlib.globals.lock.release()

                    if isusedbyother:
                        raise Exception("Channel '"+ch + "' used by another instance")
                    rv.append(ch)
        return rv

    def Power(self, value: bool) -> None:
        rol = []
        rol.append( CC2xlib.json_data.make_requestobject("getItem",CC2xlib.globals.always_monitored[0],"Control.power",''))
        rol.append( CC2xlib.json_data.make_requestobject("setItem",CC2xlib.globals.always_monitored[0],"Control.power",str(int(value))))
        CC2xlib.globals.queue_request(rol)
        
           
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
                        rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,item,v))
        return rol
      
    def getChannels(self,groupname):
        rv = []
        groups = self.jgroups['GROUP']
        for group in groups:
            for key,val in group.items():
                if key == groupname:
                    channels = val["CHANNEL"]
                    for ch in channels:
                        rv.append(ch)
        return rv


              
              
          

    def getTransitions(self):
        return self.jtransitions['TRANSITION']

           
    def SetVoltage(self, arg):
        if len(arg) != 2 :
            raise Exception('SetVoltage(arg)', 'is not a pair of objects (must be lists)')
        keys = arg[1]
        values = arg[0]
        # check channel is one of groups
        if len(keys) != len(values) :
            raise Exception('len list of values ', 'not equal len list of keys')

        rol = []

        for j in range(len(keys)):
            rol.append( CC2xlib.json_data.make_requestobject("setItem",keys[j],"Control.voltageSet",values[j]))
     
        return rol


    def getStatusJson(self):
        all = CC2xlib.globals.StatusJson()
        return ''

    
    def ApplyTransition(self,toapply):
        if (self.tw and self.tw.is_alive()):
            self.tw._delete()

        self.tw = threading.Thread(target=self.applytransitionworker, args=(toapply,))
        self.tw.start()
        


    def applytransitionworker(self,toapply):
        transitions = self.getTransitions()
        for tr in transitions:
            if toapply in tr:
                workqueue = tr[toapply]
                for nextjob in workqueue:
                    rol = []
                    for item in nextjob:
                        if (str(item).startswith("Control.") or str(item).startswith("Setup.")):
                            values = nextjob[item]
                            groups = nextjob['GROUP']
                            for group in groups:
                                channels = self.getChannels(group)
                                j = 0
                                for channel in channels:
                                    rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,item,values[j]))
                                    j = j + 1
                            CC2xlib.globals.queue_request(rol) 
                        elif str(item) != 'GROUP':
                            CC2xlib.globals.lock.acquire()
                            self.waitstring =json.dumps(nextjob)
                            CC2xlib.globals.lock.release()

                            rrlen = 1
                            
                            while rrlen:
                                CC2xlib.globals.lock.acquire()
                                #print(self.waitstring)
                                if not self.waitstring:
                                    rrlen = 0
                                CC2xlib.globals.lock.release()
                                time.sleep(0.2)

                            # wait for status or event
                            pass
        pass
     
   


a = PowerSupply()
a.init()
a.Power(True)
a.ApplyTransition("Off->On")
#rol = 
#arol = []
#arol.append(CC2xlib.json_data.make_requestobject("getItem",a.master,"Control.power",''))
#arol.append( CC2xlib.json_data.make_requestobject("setItem",a.master,"Control.power",1))
#CC2xlib.globals.queue_request(arol)

#arol = []
#arol.append( CC2xlib.json_data.make_requestobject("setItem","0_0_0","Control.channelEventMask",65535))
#arol.append( CC2xlib.json_data.make_requestobject("setItem","0_0_0","Control.voltageSet",32))
#arol.append( CC2xlib.json_data.make_requestobject("setItem","0_0_0","Control.on",1))
#arol.append(a.rolSetVoltage(([30.0],["0_0_0"])))

#CC2xlib.globals.queue_request(arol)



for i in range(30):
    time.sleep(1)


