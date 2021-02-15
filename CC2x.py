#  -*- coding: utf-8 -*-
#***************************************************************************
#* Copyright (C) 2020 by Andreas Langhoff *
#* <andreas.langhoff@frm2.tum.de> *
#* This program is free software; you can redistribute it and/or modify *
#* it under the terms of the GNU General Public License v3 as published *
#* by the Free Software Foundation; *
# **************************************************************************



import json
import copy
import threading
import time
from typing import List

from entangle import base
from entangle.core import states, Prop, Attr, Cmd, pair, listof, uint32, boolean
from entangle.device.iseg import CC2xlib
#import entangle.device.iseg.CC2xlib.globals
#import entangle.device.iseg.CC2xlib.json_data
#import entangle.device.iseg.CC2xlib.CC2xjsonhandling
from entangle.device.iseg.CC2xlib.HardLimits import HardLimits

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
        self.lastcmd = msg.rstrip()
        print('CmdProcessor.Write('+self.lastcmd + ')')
        ourcmds = ['APPLY:']
        for cmd in ourcmds:
            if self.lastcmd.startswith(cmd):
                if cmd == ourcmds[0]:
                    n_ = len(cmd)
                    tr = self.lastcmd[n_:]
                    self.applyTransition(tr)
        return len(msg)

    #def Read(self, n=0):
        # this returns always the current statuss
    #    return self._state[1]
    def ReadLine(self):
        print('CmdProcessor.ReadLine() lastcmd == ' + self.lastcmd)
        if not self.lastcmd:
            return ''
        if self.lastcmd == '?':
            return self._state[1]
        tmp = self.lastcmd.rstrip()
        cmd = 'TR'
        index = tmp.find(cmd)
        if index < 0:
            return ''
        itr = int(tmp[index+len(cmd):].strip())
        tr_names =  self.getTransitionNames()
        if not tr_names:
            return ''
        if len(tr_names) <= itr:
            return ''
        return tr_names[itr]



class IntelligentPowerSupply(CmdProcessor,base.StringIO):
    """Controls an Iseg CC2x high-voltage power supply via websocket.
       Iseg CC2x accepts command via the entangle StringIO interface
    """

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
                disallowed = ( states.INIT,
                              states.UNKNOWN,)),

        'getChannels':
            Cmd('gets channel list for a group.',
                str,listof(str),'group name','list of channels',
                disallowed = (states.INIT,
                              states.UNKNOWN,)),
        'getTransitionNames':
            Cmd('gets list of transition names.',
                None,listof(str),'None','transition names',
                disallowed = (states.INIT,
                              states.UNKNOWN,)),

        'applyTransition':
            Cmd('applies a transition like Off->On, On->Off etc.',
                str,None, 'transition name', 'None',
                disallowed = (states.BUSY,states.FAULT,states.INIT,states.OFF)),



    }


    properties = {
        'address': Prop(str, 'ip address of device.'),
        'user': Prop(str, 'user.'),
        'password': Prop(str, 'pw.'),
        'transitions': Prop(str, 'transitions.',default=''),
        'groups': Prop(str, 'groups.'),
        'operatingstyles': Prop(str, 'operatingstyles.',default=''),
        'tripeventallmodulesoff': Prop(boolean, 'operatingstyles.',default=False),
    }
    attributes = {
         'jsonstatus':   Attr(str,'',writable = False,memorized = False),
    }

    def init(self):
        self._state = (states.INIT,self.address)
        #checkoperatingstates(operatingstates)
        self.channels_handled = self.checkchannels()
        self.waitstring =''
        self.waitstringmintime = ''
        self.tw = None

        # these are accessed in writing also from other thread, so do the proper locking:
        # self.waitstring
        # self.waitstringmintime
        # self._state


        CC2xlib.globals.CRATE.lock.acquire()
        CC2xlib.globals.HardLimits.tripEventAllModulesOff = self.tripeventallmodulesoff
        CC2xlib.globals.CRATE.instances.append(self)
        CC2xlib.globals.CRATE.lock.release()
        CC2xlib.globals.add_monitor(self.address,self.user,self.password)

    def rolisAlive(self):
        print("CC2x.IntelligentPowerSupply.rolisAlive")
        rol = []
        rol.extend(self.setOperatingStylesOrCommand())
        return rol


    def safequeue(self, rol):
        rv, msg =  CC2xlib.globals.HardLimits.checkmovelimitsandbugfix(rol)
        if rv:
            CC2xlib.globals.CRATE.lock.acquire()
            #self._state  =(self._state[0], msg +self._state[1]) no change of _state[1] as waitstring
            print(msg +self._state[1])
            CC2xlib.globals.CRATE.lock.release()
        CC2xlib.globals.queue_request(rol)

    def setOperatingStylesOrCommand(self):
        rol = []
        groupnames = CC2xlib.CC2xjsonhandling.getGroupNames(self.groups)
        for groupname in groupnames:
            rol.extend(self.rolsetOperatingStyleOrCommand(groupname))
        return rol


    def rolsetOperatingStyleOrCommand(self,groupname:str):
        rol = []
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
                                                #if any(c.isalpha() for c in str(v)):
                                                #    strvalue = str(v)
                                                #else:
                                                #    strvalue = str(float(v))
                                                rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,item,v))

                        elif cmds != 'CHANNEL':
                            for channel in channels:
                                cmdvalue = val[cmds]
                                rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,cmds,str(cmdvalue)))
        return rol




    def delete(self):
        #print("CC2x.delete")
        n_instances = 0
        CC2xlib.globals.CRATE.lock.acquire()
        for i in CC2xlib.globals.CRATE.instances:
            if i == self :
                CC2xlib.globals.CRATE.instances.remove(i)
                n_instances = len(CC2xlib.globals.CRATE.instances)
        CC2xlib.globals.CRATE.lock.release()
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
                    CC2xlib.globals.CRATE.lock.acquire()
                    for i in CC2xlib.globals.CRATE.instances:
                        if i != self:
                            if ch in i.channels_handled:
                                isusedbyother = True

                    CC2xlib.globals.CRATE.lock.release()

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
        CC2xlib.globals.CRATE.lock.acquire()
        tmp = self.transitions[:]
        CC2xlib.globals.CRATE.lock.release()
        return CC2xlib.CC2xjsonhandling.getTransitionNames(tmp)

    def getTransitions(self):

        tmp =''
        CC2xlib.globals.CRATE.lock.acquire()
        tmp = self.transitions[:]
        CC2xlib.globals.CRATE.lock.release()
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
        # pylint: disable=consider-using-enumerate
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

        CC2xlib.globals.CRATE.lock.acquire()
        if self._state[0] in  [states.INIT, states.UNKNOWN]:
            self._state = copy.deepcopy(CC2xlib.globals.CRATE._state)
        if CC2xlib.globals.CRATE._state[0] in  [states.OFF, states.ALARM] :
            self._state =  copy.deepcopy(CC2xlib.globals.CRATE._state)
        if CC2xlib.globals.CRATE._state[0]  == states.ON:
            if self._state[0] not in [states.BUSY, states.ALARM, states.FAULT] :
                self._state =  copy.deepcopy(CC2xlib.globals.CRATE._state)
                self._state = (CC2xlib.globals.CRATE._state[0], self._state[1])
        CC2xlib.globals.CRATE.lock.release()

        strvoltages = CC2xlib.globals.VoltagesJson(self.channels_handled)

        fullinfostate = copy.deepcopy(self._state)
        fullinfostate = (fullinfostate[0] ,fullinfostate[1] + "  " + strvoltages)
        return fullinfostate




    def applyTransition(self,toapply):
        if (self.tw) and (self.tw.is_alive()):
            self.tw.join()
        self.tw = threading.Thread(target=self.applytransitionworker, args=(toapply,))
        self.tw.daemon = True
        self.tw.start()

    def applytransitionworker(self,toapply):
        doreturn = 0
        CC2xlib.globals.CRATE.lock.acquire()
        self._state = (states.BUSY,"START:"+toapply)
        CC2xlib.globals.CRATE._state =(states.ON,"CONNECTED : "+CC2xlib.globals.CRATE.sessionid)
        print(self._state[1])
        CC2xlib.globals.CRATE.lock.release()

        transitions = self.getTransitions()
        for tr in transitions:
            if toapply in tr:
                workqueue = tr[toapply]
                changemsg = ''
                for nextjob in workqueue: # here just a HardLimits parameter check and adjust
                    for item in nextjob:
                        if str(item) == 'GROUP' :
                            continue
                        getrol = []
                        if (str(item).startswith("Control.") or str(item).startswith("Setup.")):
                            values = nextjob[item]
                            groups = nextjob['GROUP']
                            for groupname in groups:
                                channels = CC2xlib.CC2xjsonhandling.getChannels(self.groups,groupname)
                                j = 0
                                for channel in channels:
                                    rol = []
                                    rol.append(CC2xlib.json_data.make_requestobject("setItem",channel,item,values[j]))
                                    rv, msg = HardLimits.checkmovelimitsandbugfix(rol)
                                    if rv:
                                        if changemsg:
                                            changemsg += ", "
                                        changemsg += msg
                                        p = rol[0]['p']
                                        v = float(p['v'])
                                        values[j] = v
                                        #nextjob[item] = values , not needed, by ref already , python!
                                    j = j + 1

                if changemsg:
                    print(changemsg)
                    CC2xlib.globals.CRATE.lock.acquire()
                    self._state = (self._state[0], self._state[1] + " : "+changemsg)
                    CC2xlib.globals.CRATE.lock.release()
                #here we actually elaborate the workjobs
                for nextjob in workqueue:
                    for item in nextjob:
                        if str(item) == 'GROUP' :
                            continue
                        getrol = []
                        # we wait for response, but by sending a "getItem" we force a response
                        #  which would not come if condition already reached
                        values = nextjob[item]
                        groups = nextjob['GROUP']
                        for groupname in groups:
                            if CC2xlib.globals.ctrlcreceived:
                                return
                            channels = CC2xlib.CC2xjsonhandling.getChannels(self.groups,groupname)
                            j = 0
                            for channel in channels:
                                getrol.append(CC2xlib.json_data.make_requestobject("getItem",channel,item))
                                j = j + 1


                        CC2xlib.globals.CRATE.lock.acquire()
                        if self._state[0] == states.ALARM:
                            doreturn = 1
                        else:
                            self.waitstring =json.dumps(nextjob)
                            self.waitstringmintime = ''
                        CC2xlib.globals.CRATE.lock.release()

                        if doreturn:
                            return

                        CC2xlib.globals.CRATE.lock.acquire()
                        if not (str(item).startswith("Control.") or str(item).startswith("Setup.")):
                            self.statusstr = "WAITFOR_CONDITION:"+str(nextjob)
                            self._state = (states.BUSY,self.statusstr)
                            print(self.statusstr)
                        CC2xlib.globals.CRATE.lock.release()

                        waitforanswer = True

                        if str(item) in ["Control.clearEvents", "Control.clearAll", "Control.clearErrors"]:
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

                                CC2xlib.globals.CRATE.lock.acquire()
                                if CC2xlib.globals.CRATE._state[0] == states.ALARM:
                                    doreturn = 1
                                if not CC2xlib.globals.CRATE.poweron:
                                    doreturn = 1
                                if not doreturn:
                                    self.statusstr = "QUEUE_REQUEST:"+str(nextjob)
                                    self._state =(states.BUSY,self.statusstr)
                                    print(self.statusstr)
                                CC2xlib.globals.CRATE.lock.release()
                                if doreturn:
                                    return
                                self.safequeue(rol)

                        if not waitforanswer:
                            CC2xlib.globals.CRATE.lock.acquire()
                            self.waitstring = ''
                            time.sleep(2)  # needed to avoid  crate firmware sloppyness (Status.ramping 1 comes only after litte delay)
                            CC2xlib.globals.CRATE.lock.release()

                        rrlen = 1
                        while rrlen:
                            CC2xlib.globals.CRATE.lock.acquire()
                            if CC2xlib.globals.CRATE._state[0] == states.ALARM:
                                self._state = copy.deepcopy(CC2xlib.globals.CRATE._state)
                                doreturn = 1
                            if not CC2xlib.globals.CRATE.poweron:
                                doreturn = 1
                            CC2xlib.globals.CRATE.lock.release()
                            if doreturn:
                                return
                            time.sleep(2)  # a bit hacky!

                            CC2xlib.globals.CRATE.lock.acquire()
                            if not self.waitstring:
                                rrlen = 0
                            CC2xlib.globals.CRATE.lock.release()



                CC2xlib.globals.CRATE.lock.acquire()
                if CC2xlib.globals.CRATE._state[0] == states.ALARM:
                    #self.statusstr = CC2xlib.globals.CRATE._state[1]
                    doreturn = 1
                if not CC2xlib.globals.CRATE.poweron:
                    doreturn = 1
                if not doreturn:
                    CC2xlib.globals.CRATE._state = (CC2xlib.globals.CRATE._state[0],"FINISHED:"+toapply)
                    self._state = copy.deepcopy(CC2xlib.globals.CRATE._state)
                    print(CC2xlib.globals.CRATE._state)
                CC2xlib.globals.CRATE.lock.release()
                return
