#  -*- coding: utf-8 -*-
#***************************************************************************
#* Copyright (C) 2020 by Andreas Langhoff *
#* <andreas.langhoff@frm2.tum.de> *
#* This program is free software; you can redistribute it and/or modify *
#* it under the terms of the GNU General Public License v3 as published *
#* by the Free Software Foundation; *
# **************************************************************************


import json
import threading
import time
from typing import List

from entangle import base
from entangle.core import states ,int32, Prop, Attr, Cmd, pair,listof,uint32
from  entangle.device.iseg import CC2xlib
import entangle.device.iseg.CC2xlib.globals
import entangle.device.iseg.CC2xlib.json_data
import entangle.device.iseg.CC2xlib.CC2xjsonhandling


class CmdProcessor(object):
    lastcmd = ''
    def read_availableLines(self):
        tr_names =  self.getTransitionNames()
        if not tr_names:
            return 0
        return len(tr_names)

    def read_availableChars(self):
        return -1

    def Write(self, msg:str)->uint32:
        self.lastcmd = msg
        ourcmds = ['APPLY:']
        for cmd in ourcmds:
            if msg.startswith(cmd):
                if cmd == ourcmds[0]:
                    n_ = len(cmd)
                    tr = self.lastcmd[n_:]
                    self.applyTransition(tr)
        return len(msg)

    def ReadLine(self):
        if not self.lastcmd:
            return ''
        tmp = self.lastcmd.rstrip()
        cmd = 'TR'
        index = tmp.find(cmd)
        if index < 0:
            return ''
        itr = int(tmp[index+len(cmd):].strip())
        tr_names =  self.getTransitionNames()
        if not tr_names:
            return ''
        if len(tr_names) < itr:
            return ''
        return tr_names[itr]



class IntelligentPowerSupply(CmdProcessor,base.StringIO):
    """Controls an Iseg CC2x high-voltage power supply via websocket."""
    
    commands = {
        'setVoltage':
            Cmd('Sets Voltage for a multiple channels.',
                pair(listof(float), listof(str)) , None,
                '[channel1,channel2,...][voltage1,voltage2,..]',
                'None',
                disallowed= (states.BUSY, states.FAULT, states.INIT, states.OFF,
                            states.UNKNOWN,)),
        'getGroupNames':
            Cmd('gets group names.',
                None,listof(str),'group names',None,
                disallowed = ( states.FAULT, states.INIT,
                              states.UNKNOWN,)),

        'getChannels':
            Cmd('gets channel list for a group.',
                str,listof(str),'group name','list of channels',
                disallowed = (states.FAULT, states.INIT,
                              states.UNKNOWN,)),
        'getTransitionNames':
            Cmd('gets list of transition names.',
                None,listof(str),'None','transition names',
                disallowed = (states.FAULT, states.INIT,
                              states.UNKNOWN,)),
       
        'applyTransition':
            Cmd('applies a transition like Off->On, On->Off etc.',
                str,None, 'transition namé', 'None',
                disallowed = (states.BUSY,states.FAULT,states.INIT,states.OFF)),

       

    }

    
    properties = {
        'address': Prop(str, 'ip address of device.'),
        'user': Prop(str, 'user.'),
        'password': Prop(str, 'pw.'),
        'transitions': Prop(str, 'transitions.',default=''),
        'groups': Prop(str, 'groups.'),
        'operatingstyles': Prop(str, 'operatingstyles.',default=''),
        'unitTime': Prop(str, 'unitTime.'),
        'unitCurrent': Prop(str, 'unitCurrent.'),
        'maxTripCurrent': Prop(int32, 'maxTripCurrent.'),
        'maxVoltage': Prop(int32, 'maxVoltage.')
    }
   
    attributes = {
         'jsonstatus':   Attr(str,'',writable = False,memorized = False),
    }
 
    def init(self):
        print("init")
        self._state = (states.INIT,self.address)
        #checkoperatingstates(operatingstates)
        self.channels_handled = self.checkchannels()
        self.waitstring =''
        self.waitstringmintime = ''
        self.tw = None

        # accessed also from other thread, so do the proper locking:
        # self.channels_handled
        # self.waitstring
        # self.waitstringmintime
        CC2xlib.globals.lock.acquire()
        CC2xlib.globals.instances.append(self)
        CC2xlib.globals.lock.release()
        CC2xlib.globals.add_monitor(self.address,self.user,self.password)
        
        
        rol = []
        rol.append( CC2xlib.json_data.make_requestobject("getItem",CC2xlib.globals.always_monitored[0],"Status.power"))
        self.safequeue(rol)
        self.setOperatingStylesOrCommand()
        
    def safequeue(self, rol):
        if self.checkmovelimitsandbugfix(rol):
            self._state  =(self._state[0], "LIMITS MOVED, "+self._state[1])
        CC2xlib.globals.queue_request(rol)
        

    def setOperatingStylesOrCommand(self):
        groupnames = CC2xlib.CC2xjsonhandling.getGroupNames(self.groups)
        for groupname in groupnames:
            self.rolsetOperatingStyleOrCommand(groupname)
       
    
    def rolsetOperatingStyleOrCommand(self,groupname:str):
              
        channels = CC2xlib.CC2xjsonhandling.getChannels(self.groups,groupname)
        jgroups = json.loads(self.groups)
        for group in jgroups['GROUP']:
            for key,val in group.items():
            #must keep val , otherwise different assignment to key, pylint will report a warning -> dead wrong
                if key == groupname:
                    for cmds in val:
                        if cmds == "OPERATINGSTYLE":
                            operatingstyle = val["OPERATINGSTYLE"]
                            jstyles = json.loads(self.operatingstyles)
                            availablestyes = jstyles['OPERATNGSTYLE']
                            for style in availablestyes:
                                for k in style:
                                    if k == operatingstyle:
                                        items = style[k]
                                        for item,v in items.items():
                                            for channel in channels:
                                                rol = []
                                                #if any(c.isalpha() for c in str(v)):
                                                #    strvalue = str(v)
                                                #else:
                                                #    strvalue = str(float(v))
                                                rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,item,v))
                                                self.safequeue(rol)
                            
                        elif cmds != 'CHANNEL':
                            for channel in channels:
                                rol = []
                                cmdvalue = val[cmds]
                                rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,cmds,str(cmdvalue)))
                                self.safequeue(rol)

                       
                                
               
                            

  
    def delete(self):
        print("CC2x.delete")
        n_instances = 0
        CC2xlib.globals.lock.acquire()
        for i in CC2xlib.globals.instances:
            if i == self :
                CC2xlib.globals.instances.remove(i)
                n_instances = len(CC2xlib.globals.instances)
        CC2xlib.globals.lock.release()
        if not n_instances:
            CC2xlib.globals.reset()
        

    


    
    def checkchannels(self):
        rv = []
        jobjgroups = json.loads(self.groups)
        groups = jobjgroups['GROUP']
        for group in groups:
            for groupname in group:
                channels = CC2xlib.CC2xjsonhandling.getChannels(self.groups,groupname)
                for ch in channels:
                    if ch in rv:
                        raise Exception("Duplicate channel '"+ch + "' in 'GROUP':"+group)

                    isusedbyother = False
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

    def getChannels(self,groupname):
        return CC2xlib.CC2xjsonhandling.getChannels(self.groups,groupname)
        

    def On(self):
        CC2xlib.globals.power(True)

    def Off(self):
        CC2xlib.globals.power(False)
        if self.tw:
            self.tw.join()
    

    def getGroupNames(self)->List[str]:
        return CC2xlib.CC2xjsonhandling.getGroupNames(self.groups)
       


    def getTransitionNames(self):
        tmp =''
        CC2xlib.globals.lock.acquire()
        tmp = self.transitions[:]
        CC2xlib.globals.lock.release()
        return CC2xlib.CC2xjsonhandling.getTransitionNames(tmp)

    def getTransitions(self):

        tmp =''
        CC2xlib.globals.lock.acquire()
        tmp = self.transitions[:]
        CC2xlib.globals.lock.release()
        if not tmp:
            return []
        return CC2xlib.CC2xjsonhandling.getTransitions(tmp)
        

    def setVoltage(self, arg):
        if len(arg) != 2 :
            raise Exception('SetVoltage(arg)', 'is not a pair of objects (must be lists)')
        keys = arg[1]
        values = arg[0]
        
        # check channel is one of groups
        if len(keys) != len(values) :
            raise Exception('len list of values ', 'not equal len list of keys')

        rol = []

        for j in range(len(keys)):
            print("key="+ str(keys[j]) + ", value="+str(values[j]) )
            rol.append( CC2xlib.json_data.make_requestobject("getItem",keys[j],"Control.voltageSet",''))
            rol.append( CC2xlib.json_data.make_requestobject("setItem",keys[j],"Control.voltageSet",values[j]))
        self.safequeue(rol)
        
        

    def read_jsonstatus(self):
        ours = CC2xlib.globals.StatusJson(self.channels_handled)
        return ours

    def get_jsonstatus_unit(self):
        return ''
    def state(self):
        currstate = (states.UNKOWN,'unknown')
        CC2xlib.globals.lock.acquire()
        currstate = self._state
        CC2xlib.globals.lock.release()
        return currstate

    def checkmovelimitsandbugfix(self, rol):
        cmds = ["Control.voltageSet","Control.currentSet","Setup.delayedTripTime"]
        limits = [self.maxVoltage, self.maxTripCurrent,0]
        units = ['',self.unitCurrent,self.unitTime]
        #units is a bug fix for iges ics
        limitsmoved = 0
        
        for ro in rol:
            if ro['c'] == "setItem":
                item = ro['p']
                if not 'i' in item:
                    continue
                ourcmd = item['i']
                if ourcmd in cmds:
                    i = cmds.index( ourcmd)
                    v = item['v']
                    sign = 1
                    if v < 0:
                        sign = -1
                    if limits[i]:
                        if abs(v) > limits[i]:
                            item['v'] = sign * limits[i]
                            limitsmoved = 1
                    if units[i]:
                        item['u'] = units[i]
                           
        return limitsmoved


    def applyTransition(self,toapply):
        if (self.tw) and (self.tw.is_alive()):
            self.tw.join()
        self.tw = threading.Thread(target=self.applytransitionworker, args=(toapply,))
        self.tw.daemon = True
        self.tw.start()

    def applytransitionworker(self,toapply):
        CC2xlib.globals.lock.acquire()
        self._state = (states.BUSY,"START:"+toapply)
        print(self._state[1])
        CC2xlib.globals.lock.release()
        transitions = self.getTransitions()
        for tr in transitions:
            if toapply in tr:
                workqueue = tr[toapply]
                #here we actually elaborate the workjobs
                for nextjob in workqueue:
                    
                    for item in nextjob:
                        
                        if(str(item) == 'GROUP') :
                            continue
                        getrol = []
                        # we wait for response, but by sending a "getItem" we force a response which would not come if condition already reached
                        groups = nextjob['GROUP']
                        for groupname in groups:
                            if CC2xlib.globals.ctrlcreceived:
                                return
                            channels = CC2xlib.CC2xjsonhandling.getChannels(self.groups,groupname)
                            j = 0
                            for channel in channels:
                                getrol.append(CC2xlib.json_data.make_requestobject("getItem",channel,item))
                                j = j + 1
                        
                            
                        CC2xlib.globals.lock.acquire()
                        self.waitstring =json.dumps(nextjob)
                        self.waitstringmintime = ''
                        if not (str(item).startswith("Control.") or str(item).startswith("Setup.")):
                            self.statusstr = "WAITFOR_CONDITION:"+str(nextjob)
                            self._state = (states.BUSY,self.statusstr)
                            print(self.statusstr)
                        CC2xlib.globals.lock.release()

                        waitforanswer = True
                        
                        if str(item) == "Control.clearEvents":
                            waitforanswer = False

                        if waitforanswer:
                            self.safequeue(getrol) 

                        if (str(item).startswith("Control.") or str(item).startswith("Setup.")):
                            
                            values = nextjob[item]
                            groups = nextjob['GROUP']
                            for groupname in groups:
                                channels = CC2xlib.CC2xjsonhandling.getChannels(self.groups,groupname)
                                j = 0
                                rol = []
                                for channel in channels:
                                    rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,item,values[j]))
                                    j = j + 1

                                do_break = 0
                                CC2xlib.globals.lock.acquire()
                                if not CC2xlib.globals.poweron:
                                    do_break = 1
                                if self._state == states.FAULT:
                                    do_break = 1

                                CC2xlib.globals.lock.release()
                                if do_break:
                                    break
                                CC2xlib.globals.lock.acquire()
                                self.statusstr = "QUEUE_REQUEST:"+str(nextjob)
                                self._state =(states.BUSY,self.statusstr)
                                print(self.statusstr)
                                CC2xlib.globals.lock.release()
                                self.safequeue(rol)
                               
                        if not waitforanswer:
                            CC2xlib.globals.lock.acquire()
                            self.waitstring = ''
                            CC2xlib.globals.lock.release()

                        rrlen = 1
                        while rrlen:
                            doreturn = 0
                            CC2xlib.globals.lock.acquire()
                            if not CC2xlib.globals.poweron:
                                doreturn = 1
                            CC2xlib.globals.lock.release()
                            if doreturn:
                                return
                            time.sleep(2)  # a bit hacky!

                            CC2xlib.globals.lock.acquire()
                            if self._state == states.FAULT :
                                doreturn = 1
                            if not self.waitstring:
                                rrlen = 0
                            CC2xlib.globals.lock.release()
                            if doreturn:
                                return  
                
                CC2xlib.globals.lock.acquire()
                self.statusstr = "FINISHED:"+toapply
                if CC2xlib.globals.poweron:
                    self._state = (states.ON,self.statusstr)
                else :
                    self._state = (states.OFF,self.statusstr)
                print(self.statusstr)
                CC2xlib.globals.lock.release()
                return
        
     
   



