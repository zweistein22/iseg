#  -*- coding: utf-8 -*-
#***************************************************************************
#* Copyright (C) 2020 by Andreas Langhoff *
#* <andreas.langhoff@frm2.tum.de> *
#* This program is free software; you can redistribute it and/or modify *
#* it under the terms of the GNU General Public License v3 as published *
#* by the Free Software Foundation; *
# **************************************************************************


from entangle import base
from entangle.core import states
from  entangle.device.iseg import CC2xlib
import entangle.device.iseg.CC2xlib.globals
import entangle.device.iseg.CC2xlib.json_data
import entangle.device.iseg.CC2xlib.CC2xjsonhandling

class PowerSupply(base.PowerSupply):


    def init(self):
        self._state = (states.INIT,self.address)
        self.channels_handled = [self.channel]
        self.waitstring =''
        self.waitstringmintime = ''
        CC2xlib.globals.lock.acquire()
        CC2xlib.globals.instances.append(self)
        CC2xlib.globals.lock.release()
        CC2xlib.globals.add_monitor(self.address,self.user,self.password)


    def delete(self):
        print("isegCC2xChannel.delete")
        n_instances = 0
        CC2xlib.globals.lock.acquire()
        for i in CC2xlib.globals.instances:
            if i == self :
                CC2xlib.globals.instances.remove(i)
                n_instances = len(CC2xlib.globals.instances)
        CC2xlib.globals.lock.release()
        if not n_instances:
            CC2xlib.globals.reset()

    def On(self):
        rol = []
        rol.append(CC2xlib.json_data.make_requestobject("setItem",self.channel,"Control.On",1))
        CC2xlib.globals.queue_request(rol)

    def Off(self):
        rol = []
        rol.append(CC2xlib.json_data.make_requestobject("setItem",self.channel,"Control.On",0))
        CC2xlib.globals.queue_request(rol)

    
    def getItemValue(self, cmd:str)->float:
        rv = 0
        CC2xlib.globals.lock.acquire()
        if self.channel in CC2xlib.globals.itemUpdated:
            ours = CC2xlib.globals.itemUpdated[self.channel]
            if cmd in ours:
                vu = ours[cmd]
                rv = float(vu['v'])
        CC2xlib.globals.lock.release()
        return rv


    def read_voltage(self):
        return self.getItemValue("Status.voltageMeasure")

    
    def write_voltage(self, value):
        rol = []
        rol.append(CC2xlib.json_data.make_requestobject("setItem",self.channel,"Control.voltageSet",str(value)))
        CC2xlib.globals.queue_request(rol)

    
    def read_current(self):
        return self.getItemValue("Status.currentMeasure")

    def write_current(self, value):
        rol = []
        rol.append(CC2xlib.json_data.make_requestobject("setItem",self.channel,"Control.currentSet",str(value)))
        CC2xlib.globals.queue_request(rol)

