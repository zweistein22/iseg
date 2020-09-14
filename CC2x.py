#  -*- coding: utf-8 -*-
#***************************************************************************
#* Copyright (C) 2020 by Andreas Langhoff *
#* <andreas.langhoff@frm2.tum.de> *
#* This program is free software; you can redistribute it and/or modify *
#* it under the terms of the GNU General Public License v3 as published *
#* by the Free Software Foundation; *
# **************************************************************************
import time
import json

from entangle import base
from entangle.core import states , Prop, Cmd, pair,pairsof,listof


from entangle.device.iseg.CC2xlib.globals import add_monitor, queue_request


class PowerSupply(base.MLZDevice):
    """Controls an Iseg NHQ/EHQ high-voltage power supply via string I/O."""
    
    commands = {
        'SetVoltage':
            Cmd('Sets Voltage for a group (multiple groups possible).',
                pair(listof(float), listof(str)) , None,
                '[group1,group2,...][voltage1,voltage2,..]',
                'None',
                disallowed=(states.BUSY, states.FAULT, states.INIT,
                            states.UNKNOWN,)),
    }

    
    properties = {
        'address': Prop(str, 'ip address of device.'),
        'user': Prop(str, 'user.'),
        'password': Prop(str, 'pw.'),
        'groups': Prop(str, 'groups.'),
        'operatingstates': Prop(str, 'operatingstates.'),
      }

   
 
    def init(self):
      print("Init")
      self.jgroups = json.loads(self.groups)
      #checkchannels(groups)
      self.joperatingstates = json.loads(self.operatingstates)

      for group in self.jgroups:
          #groupname = list(group.keys())[0]
          print(group)

      #checkoperatingstates(operatingstates)
      add_monitor(self.address,self.user,self.password)
      state = states.ON
   
    def setItemValue(self,groupname,item,value):
        rol = [] # request object list 
        channels = self.jgroup[groupname]['channels']
        rampstyle = self.jgroup[groupname]['operatingstate']
        for rstyle in self.joperatingstates :
            stylename = list(rstyle.keys())[0]
            if stylename == rampstyle :
                for k, v in rstyle[stylename].items():
                    item = k
                    for channel in channels :
                            rol.append(json_data.make_requestobject("setItem",channel,item,v))
        queue_request(rol)

    def SetVoltage(self, arg):
     for a in arg:
         print(str(a))
     return "ok"
      #for group in self.jgroups:
      #    groupname = list(group.keys())[0]
#         setItemValue(self,groupname,"Control.voltageSet",arg)
      #print(arg)
     # return arg

   
 #   def Stop(self):
 #     print("Stop")
 #     pass


