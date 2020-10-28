#  -*- coding: utf-8 -*-
#***************************************************************************
#* Copyright (C) 2020 by Andreas Langhoff *
#* <andreas.langhoff@frm2.tum.de> *
#* This program is free software; you can redistribute it and/or modify *
#* it under the terms of the GNU General Public License v3 as published *
#* by the Free Software Foundation; *
# **************************************************************************
import copy
import json
from entangle import base
from entangle.core import states , Prop, Attr
from  entangle.device.iseg import CC2xlib
import entangle.device.iseg.CC2xlib.globals
from entangle.device.iseg.CC2xlib.HardLimits import HardLimits

class PowerSupply(base.PowerSupply):
    properties = {
        'address': Prop(str, 'ip address of device.'),
        'user': Prop(str, 'user.'),
        'password': Prop(str, 'pw.'),
        'channel': Prop(str, 'channel.'),
        'operatingstyle': Prop(str, 'operatingstyle.',default=''),
    }

    attributes = {
         'jsonstatus':   Attr(str,'',writable = False,memorized = False),
    }

    def init(self):
        print("isegCC2cChannel.PowerSupply.init")
        self.mode = 'voltage'
        self._state = (states.INIT,self.address)
        self.channels_handled = [self.channel]
        self.waitstring =''
        self.waitstringmintime = ''
        # begin below should turn off disallowed attribute for off state, but it is not working
        tu = self.attributes['value']
        daw = list(tu.disallowed_write)
        if states.OFF in daw:
            daw.remove(states.OFF)
        tu1 = tuple(daw)
        tu.disallowed_write = tu1
        #idea: put this in __init__
        # probably attribute is read in before by deviceworker -> todo: check if time permitting.
        #end
        CC2xlib.globals.CRATE.lock.acquire()
        CC2xlib.globals.CRATE.instances.append(self)
        CC2xlib.globals.CRATE.lock.release()
        CC2xlib.globals.add_monitor(self.address,self.user,self.password)

    def rolisAlive(self):
        # this function is called once the crate is alive (= can accept parameters)
        rol = []
        print("isegCC2cChannel.PowerSupply.rolisAlive")
        jos = json.loads(self.operatingstyle)
        for item in jos:
            v = jos[item]
            rol.append(CC2xlib.json_data.make_requestobject("setItem",self.channel,item,v))
        return rol

    def delete(self):
        print("isegCC2xChannel.delete")
        n_instances = 0
        CC2xlib.globals.CRATE.lock.acquire()
        for i in CC2xlib.globals.CRATE.instances:
            if i == self :
                CC2xlib.globals.CRATE.instances.remove(i)
                n_instances = len(CC2xlib.globals.CRATE.instances)
        CC2xlib.globals.CRATE.lock.release()
        if not n_instances:
            CC2xlib.globals.reset()

    def On(self):
        print("on")
        rol = []
        self._state = (states.ON, '')
        instrol = self.rolisAlive()
        rv, msg =  CC2xlib.globals.HardLimits.checkmovelimitsandbugfix(instrol)
        if rv:
             self._state  =(self._state[0], msg +self._state[1])
        rol.extend(instrol)
        rol.append(CC2xlib.json_data.make_requestobject("setItem",self.channel,"Control.on",1))
        CC2xlib.globals.queue_request(rol)



    def Off(self):
        print("off")
        rol = []
        rol.append(CC2xlib.json_data.make_requestobject("setItem",self.channel,"Control.on",0))
        CC2xlib.globals.queue_request(rol)


    def getItemValue(self, cmd:str)->float:
        rv = 0
        CC2xlib.globals.CRATE.lock.acquire()

        if self.channel in CC2xlib.globals.CRATE.itemUpdated:
            ours = CC2xlib.globals.CRATE.itemUpdated[self.channel]
            if cmd in ours:
                vu = ours[cmd]
                rv = float(vu['v'])
        CC2xlib.globals.CRATE.lock.release()
        return rv


    def read_voltage(self):
        return self.getItemValue("Status.voltageMeasure")


    def write_voltage(self, value):
        rol = []
        rol.append(CC2xlib.json_data.make_requestobject("setItem",self.channel,"Control.voltageSet",str(value)))
        rv, msg =  HardLimits.checkmovelimitsandbugfix(rol)
        if rv:
            self._state  =(self._state[0], msg +self._state[1])
        CC2xlib.globals.queue_request(rol)


    def read_current(self):
        return self.getItemValue("Status.currentMeasure")

    def write_current(self, value):
        if self.mode == 'current':
           rol = []
           rol.append(CC2xlib.json_data.make_requestobject("setItem",self.channel,"Control.currentSet",str(value)))
           CC2xlib.globals.queue_request(rol)


    def read_jsonstatus(self):
        ours = CC2xlib.globals.StatusJson(self.channels_handled)
        return ours

    def get_jsonstatus_unit(self):
        return ''
    def state(self):
        currstate = (states.UNKNOWN,'unknown')
        CC2xlib.globals.CRATE.lock.acquire()

        if self.channel in CC2xlib.globals.CRATE.itemUpdated:
            ouritems = CC2xlib.globals.CRATE.itemUpdated[self.channel] #  all messages for channel
            #print(ouritems)
            for item in ouritems:
                vu = ouritems[item]
                if not 'v' in vu:
                    continue
                v = vu['v']
                if item == 'Status.runningState':
                    if str(v) == 'ok':
                        self._state = (states.ON, self._state[1])
                    if str(v) == 'off':
                        self._state = (states.OFF, self._state[1])
                if item == 'Control.on':
                    if str(v) == '1':
                        self._state = (states.ON, self._state[1])
                    if str(v) == '0':
                        self._state = (states.OFF, self._state[1])
                if item == 'Event.currentTrip':
                    if str(v) == '1':
                         self._state = (states.ALARM,CC2xlib.globals.CRATE._state[1])

            if 'Status.ramping' in ouritems: # effectively ovveriding previous choice
                vu = ouritems['Status.ramping']
                if 'v' in vu:
                    v = vu['v']
                    if str(v) == '1':
                            self._state = (states.BUSY, self._state[1])




        if CC2xlib.globals.CRATE._state[0] in [states.INIT, states.UNKNOWN]:
            self._state = (self._state[0], "Wait...")
        else:
            if self._state[1] == "Wait...":
                self._state = (self._state[0],'')
        currstate =  self._state  # copy.deepcopy(self._state)
        CC2xlib.globals.CRATE.lock.release()
        return currstate
      #  return self._state # not good as global listen function can change this value (running in another thread)
