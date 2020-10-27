#  -*- coding: utf-8 -*-
#***************************************************************************
#* Copyright (C) 2020 by Andreas Langhoff *
#* <andreas.langhoff@frm2.tum.de> *
#* This program is free software; you can redistribute it and/or modify *
#* it under the terms of the GNU General Public License v3 as published *
#* by the Free Software Foundation; *
# **************************************************************************
import atexit
import signal
import copy
import json
import time
from concurrent.futures import TimeoutError as ConnectionTimeoutError
import base64
import os
import inspect
from os.path import expanduser
import threading

import asyncio
import aiohttp
import websockets

from entangle.core import states


from entangle.device.iseg import CC2xlib
from entangle.device.iseg.CC2xlib import json_data
from entangle.device.iseg.CC2xlib import CC2xjsonhandling
from entangle.device.iseg.CC2xlib.HardLimits import HardLimits

port = '8080'

class CRATE:
    instances = []
    always_monitored = ['0_1000_','__']
    lock = threading.Lock()
    last_reqobj = ''
    sessionid = ''
    websocket = None
    itemUpdated = {}
    _state = (states.UNKNOWN,"uninitialized")
    poweron = False
    loop = None

def StatusJson(channellist)->str:
    rv = ''
    tmp = {}
    CRATE.lock.acquire()
    for ch in channellist:
        if ch in CRATE.itemUpdated:
            tmp[ch] = CRATE.itemUpdated[ch]
    rv = json.dumps(tmp)
    CRATE.lock.release()
    return rv

ctrlcreceived = 0

async def heartbeat(connection):
    while True:
        try:
            await asyncio.sleep(8)
            rol = []
            CRATE.lock.acquire()
            rol.append(json_data.make_requestobject("getUpdate", CRATE.always_monitored[0],''))
            r = json_data.request(CRATE.sessionid,rol)
            CRATE.last_reqobj = r
            CRATE.lock.release()
            #print("heartbeat!!!")
            await connection.send(r)
        except websockets.exceptions.ConnectionClosed:
            CRATE.lock.acquire()
            CRATE._state = (states.FAULT, 'Connection with server closed.')
            CRATE.lock.release()
            print(CRATE._state[1])
            break
        except Exception as inst:
            print("heartbeat")
            print(type(inst))    # the exception instance
            print(inst.args)     # arguments stored in .args
            print(inst)
            break
    return


async def listen(connection):
    while True:
        try :
            response = await connection.recv()
            #print("\r\n"+response)
            dictlist = json.loads(response)

            if "d" in dictlist:
                data  = dictlist["d"]
                if "file" in dictlist:
                    filename = dictlist["file"]
                    databytes = base64.b64decode(data)
                    scriptfile = inspect.getframeinfo(inspect.currentframe()).filename
                    writeablepath = os.path.dirname(os.path.abspath(scriptfile))
                    client = connection.remote_address
                    clientstr = ''
                    s = str(client[0]).replace('.','_').replace(':','_')
                    clientstr += s
                    clientstr += '_'
                    if not os.access(writeablepath, os.W_OK | os.X_OK):
                        writeablepath = expanduser("~")

                    fullpath = os.path.join(writeablepath,clientstr+filename)

                    with open(fullpath, "wb") as file:
                        file.write(databytes)
                        print(fullpath)
                    continue

            for adict in dictlist:
                #print(adict)
                if "trigger" in dictlist:
                    if dictlist["trigger"] == "false":
                        print("\r\n")
                        print("REQUEST\r\n")
                        CRATE.lock.acquire()
                        print(CRATE.last_reqobj)
                        CRATE.lock.release()
                        print("RESPONSE\r\n")
                        print(dictlist)
                        print("\r\n")

                if "t" in adict:
                    #if adict["t"] == "info":
                       # print(adict)

                    #if adict["t"] == "response":
                    #    print(adict)

                    if "c" in adict:
                        contentlist = adict["c"]
                        #print("contentlist len="+str(len(contentlist)))
                        for c in contentlist:
                            lac = CC2xlib.json_data.getshortlac(c["d"]["p"])
                            timestamp = c["d"]["t"]
                            someinstancesubscribed = 0
                            CRATE.lock.acquire()
                            for inst in CRATE.instances:
                                if lac in  inst.channels_handled:
                                    someinstancesubscribed = 1
                            CRATE.lock.release()
                            if (someinstancesubscribed or (lac in CRATE.always_monitored)):
                                command = c["d"]["i"]
                                if not ( command in ["Status.voltageTerminalMeasure", \
                                                        "Status.heartBeat","System.time","Status.temperature0", \
                                                        "Status.temperature1", "Status.currentMeasure"]):  #    , "Status.voltageMeasure"]):
                                    #print(c["d"])
                                    pass
                                if command in ["Status.inputError"]:
                                    print("\r\n")
                                    print("REQUEST\r\n")
                                    CRATE.lock.acquire()
                                    print(CRATE.last_reqobj)
                                    CRATE.lock.release()
                                    print("RESPONSE\r\n")
                                    print(dictlist)
                                    print("\r\n")
                                value = c["d"]["v"]
                                unit =  c["d"]["u"]
                                vu = {"v":value, "u": unit}
                                if ctrlcreceived:
                                    await logout()
                                    await connection.close()
                                    break

                                if lac == CRATE.always_monitored[1]:
                                    maxconnections = 3
                                    #NOT SURE : BUG in iseg module, will report disconnected clients only with a delay
                                    #doing several Reset() within short time the number of connected clients will temporarily increase
                                    if (command == "Status.connectedClients" and int(value) > maxconnections):
                                        print("only "+str(maxconnections)+ " client(s) connection allowed.")
                                        await logout()
                                        await connection.close()
                                        break

                                ourdict = {}
                                CRATE.lock.acquire()
                                if lac in CRATE.itemUpdated:
                                    ourdict = CRATE.itemUpdated[lac]
                                # this is a dict again, and that we will update
                                ourdict[command] = vu
                                CRATE.itemUpdated[lac] = ourdict
                                CRATE.lock.release()

                                if lac == CRATE.always_monitored[0]:
                                    if command == "Status.power":
                                        CRATE.lock.acquire()
                                        if  value == '0':
                                            CRATE.poweron = False
                                            CRATE._state = (states.OFF,CRATE._state[1])
                                            for inst in CRATE.instances: # all clients are also off then
                                                inst._state = (CRATE._state[0], inst._state[1])
                                        else :
                                            CRATE.poweron = True


                                            # we set _state only in isAlive delayed thread
                                        CRATE.lock.release()
                                    if command == "Status.isAlive":
                                        rol = []
                                        CRATE.lock.acquire()
                                        if  value == '0':
                                            print("Status.isAlive == 0")
                                            CRATE._state = (states.UNKNOWN,command)
                                        else :
                                            print("Status.isAlive == 1")
                                            rol.append( CC2xlib.json_data.make_requestobject("getItem",CC2xlib.globals.CRATE.always_monitored[0],"Status.power"))
                                            CRATE._state = (states.INIT,command)
                                            for inst in CRATE.instances:
                                                inst._state = copy.deepcopy(CRATE._state)
                                        CRATE.lock.release()
                                        t = threading.Thread(target=queue_request_delayed_setstate, args=(rol,15))
                                        t.start()



                                    continue
                                CRATE.lock.acquire()
                                for inst in CRATE.instances:
                                    if inst.waitstring :
                                        if not inst.waitstringmintime:
                                            inst.waitstringmintime = timestamp
                                        obj = json.loads(inst.waitstring)
                                        allrequestedok = True
                                        for item in obj:
                                            if item =='GROUP':
                                                continue

                                            groupnames = obj['GROUP']
                                            groupname = groupnames[0]
                                            requestedvalues = obj[item]
                                            channels = inst.getChannels(groupname)
                                            k = 0

                                            for ch in channels:
                                                if ch in CRATE.itemUpdated:
                                                    od2 = CRATE.itemUpdated[ch]
                                                    if item in od2:
                                                        v = od2[item]
                                                        try:
                                                            if not v['v']:
                                                                allrequestedok = False
                                                                continue
                                                            if v['v'].isalpha():
                                                                if str(v['v']) != str(requestedvalues[k]):
                                                                    allrequestedok = False
                                                            else:
                                                                if float(v['v']) != float(requestedvalues[k]):
                                                                    allrequestedok = False

                                                            if (float(timestamp) < float(inst.waitstringmintime)):
                                                                allrequestedok = False
                                                        except Exception:
                                                            allrequestedok = False
                                                    else :
                                                        allrequestedok = False

                                                else :
                                                    allrequestedok = False

                                                k = k + 1

                                        if allrequestedok:
                                            inst._state = (inst._state[0],"FINISHED:"+inst.waitstring)
                                            print(inst._state[1])
                                            inst.waitstring = ''
                                            inst.waitstringmintime = ''

                                        if not CRATE.poweron:
                                            inst._state = (CRATE._state[0],"CANCELLED:"+inst.waitstring)
                                            print(inst._state[1])
                                            inst.waitstring = ''
                                            inst.waitstringmintime = ''
                                CRATE.lock.release()

                                if  command in ["Error.currentLimitExceeded", "Event.currentTrip", \
                                                "Event.arc", "Error.arc"]:
                                    if int(value):  # for these commands we know that value can be converted to int
                                        CRATE.lock.acquire()
                                        print("\r\n")
                                        alarmmsg = lac + " : "+ command
                                        print(alarmmsg)
                                        print("\r\n")
                                        if lac in CRATE.itemUpdated:
                                            ouritems = CRATE.itemUpdated[lac]
                                            if 'Status.currentMeasure' in ouritems:
                                                vu2 = ouritems['Status.currentMeasure']
                                                if 'v' in vu2:
                                                    v = vu2['v']
                                                    alarmmsg += " "
                                                    alarmmsg += str(v)
                                                if 'u' in vu2:
                                                    u = vu2['u']
                                                    alarmmsg += str(u)

                                        CRATE._state = (states.ALARM,alarmmsg)
                                        rol = []
                                        for inst in CRATE.instances:
                                            if lac in inst.channels_handled:
                                                #inst._state = copy.deepcopy(CRATE._state)
                                                if inst.waitstring:
                                                    inst._state  =(CRATE._state[0], CRATE._state[1] + " => "+"CANCELLED: "+inst.waitstring)
                                                    inst.waitstring = ''
                                                    inst.waitstringmintime = ''
                                                #print(inst._state)
                                                if HardLimits.tripEventAllModulesOff:
                                                    for ch in inst.channels_handled:
                                                        if CC2xjsonhandling.isModuleAddress(ch):
                                                            # we switch off all handled modules
                                                            rol.append( CC2xlib.json_data.make_requestobject("setItem",ch,"Control.on", '0'))
                                        CRATE.lock.release()
                                        if len(rol):
                                            t = threading.Thread(target=queue_request, args=(rol,))
                                            t.start()
                                        #queue_request(rol) # deadlocks ! can be used directly only from other thread.

        except Exception as inst:
            print(type(inst))    # the exception instance
            print(inst.args)     # arguments stored in .args
            print(inst)          # __str__ allows args to be printed directly,
            break
    CRATE.lock.acquire()
    CRATE.websocket = None
    CRATE.lock.release()

async def logout():

    try:
        wsok = 1
        CRATE.lock.acquire()
        if not CRATE.websocket:
            wsok = 0
        CRATE.lock.release()
        if not wsok:
            return
        cmd = CC2xlib.json_data.logout(CRATE.sessionid)
        await CRATE.websocket.send(cmd)
        await CRATE.websocket.close()
        CRATE.websocket = None
    except:
        pass
    if CRATE.poweron:
        CRATE._state =(states.ON,"DISCONNECTED")
    else:
        CRATE._state =(states.OFF,"DISCONNECTED")

    CRATE.lock.acquire()
    for inst in CRATE.instances:
        inst._state = (inst._state[0], "DISCONNECTED:"+inst._state[1])
    CRATE.lock.release()
    print("CRATE:" + str(CRATE._state))

async def login(address,user,password):
    timeout = 5
    global ctrlcreceived
    global port
    try:
        CRATE.websocket = await asyncio.wait_for(websockets.connect('ws://'+address+':'+port), timeout)
        cmd = CC2xlib.json_data.login(user,password)
        await CRATE.websocket.send(cmd)
        response = await CRATE.websocket.recv()
        if ctrlcreceived:
            return
        adict = json.loads(response)
        CRATE.lock.acquire()
        CRATE.sessionid = adict["i"]
        CRATE._state =(CRATE._state[0],"CONNECTED : "+CRATE.sessionid)

        for inst in CRATE.instances:
            inst._state = (inst._state[0], inst._state[1] +" "+ CRATE._state[1])
        CRATE.lock.release()


    except  ConnectionTimeoutError:
        CRATE.lock.acquire()
        CRATE.websocket = None
        CRATE._state = (states.FAULT,"Connection timeout")
        print(CRATE._state)
        for inst in  CRATE.instances:
            inst._state = copy.deepcopy(CRATE._state)  # here we overwrite the instance State

        CRATE.lock.release()


async def fetch(session, url):
    async with session.get(url,timeout = 5) as response:
        assert response.status == 200
        return await response.read()



async def getItemsInfo(address):
    async with aiohttp.ClientSession() as session:
        url = 'http://'+address+'/api/getItemsInfo'
        html = await fetch(session, url)
        scriptfile = inspect.getframeinfo(inspect.currentframe()).filename
        writeablepath = os.path.dirname(os.path.abspath(scriptfile))
        pre = address.replace('.',"_")
        pre += "_"
        if not os.access(writeablepath, os.W_OK | os.X_OK):
            writeablepath = expanduser("~")
        fullpath = os.path.join(writeablepath, pre+"getItemsInfo.xml")
        with open(fullpath, "wb") as file:
            file.write(html)
            print(fullpath)

async def getConfig():
    cmd = CC2xlib.json_data.getConfig(CRATE.sessionid)
    await CRATE.websocket.send(cmd)


async def execute_request(requestobjlist):
    cmd = CC2xlib.json_data.request(CRATE.sessionid, requestobjlist)
    CRATE.lock.acquire()
    CRATE.last_reqobj = cmd
    CRATE.lock.release()
    await CRATE.websocket.send(cmd)
    return True


monitored = []

future1 = None
future2 = None

def reset():
    global future1,future2
    if CRATE._state == states.UNKNOWN:
        return
    if CRATE.websocket and CRATE.loop:
        future = asyncio.run_coroutine_threadsafe(logout(), CRATE.loop)
        timeout = 3
        try :
            result = future.result(timeout)
            if result:
                print(result)
            print("logout call done")
        except asyncio.TimeoutError:
            CRATE.lock.acquire()
            CRATE._state = (states.FAULT,'The logout() coroutine call took too long, cancelling...')

            for inst in CRATE.instances:
                inst._state = copy.deepcopy(CRATE._state)
            print(CRATE._state[1])
            CRATE.lock.release()
            if CRATE.loop:
                CRATE.loop.call_soon_threadsafe(future.cancel)
            else:
                future.cancel()
        except Exception as exc:
            CRATE.lock.acquire()
            CRATE._state = (states.FAULT, f'The coroutine raised an exception: {exc!r}')
            for inst in CRATE.instances:
                inst._state = copy.deepcopy(CRATE._state)
            print(CRATE._state[1])
            CRATE.lock.release()

    if not (future1 and future2):
        if CRATE.loop:
            CRATE.loop.close()
        CRATE.loop = None
    if future1:
        CRATE.loop.call_soon_threadsafe(future1.cancel)

    if future2:
        CRATE.loop.call_soon_threadsafe(future2.cancel)


    while CRATE.loop:
        time.sleep(1)
    CRATE.websocket = None
    print("reset end")
    CRATE._state = (states.UNKNOWN)


def power(value: bool) -> None:
    #print("power("+str(int(value))+")")
    rol = []
    if int(value):
        CRATE.lock.acquire()
        for inst in CRATE.instances:
            inst._state = (states.INIT,CRATE._state[1])
        CRATE.lock.release()
        rol.append( CC2xlib.json_data.make_requestobject("getItem",CRATE.always_monitored[0],"Status.isAlive"))

    rol.append( CC2xlib.json_data.make_requestobject("setItem",CRATE.always_monitored[0],"Control.power",str(int(value))))

    queue_request(rol)

def monitor(address,user,password):
    global  future1, future2, monitored
    asyncio.set_event_loop(CRATE.loop)
    #ping.ping(address)
    CRATE.loop.run_until_complete(login(address,user,password))
    tmpstate = (states.UNKNOWN)
    CRATE.lock.acquire()
    tmpstate = CRATE._state
    CRATE.lock.release()
    connected = False
    for st in tmpstate:
        if st.startswith('CONNECTED'):
            connected = True

    if not connected:
        return
    CRATE.lock.acquire()
    monitored.append(address)
    CRATE.lock.release()
    CRATE.loop.run_until_complete(getItemsInfo(address))
    CRATE.loop.run_until_complete(getConfig())

    try :
        #future1 = asyncio.ensure_future(heartbeat(CRATE.websocket))
        future2 = asyncio.ensure_future(listen(CRATE.websocket))
        #CRATE.loop.run_until_complete(asyncio.gather(future1,future2))
        CRATE.loop.run_until_complete(asyncio.gather(future2))

    except:
        pass
    CRATE.loop.run_until_complete(logout())
    CRATE.lock.acquire()
    monitored.remove(address)
    #monitored = []
    #itemUpdated = {}
    CRATE.sessionid = ''
    CRATE.lock.release()
    future1 = None
    future2 = None
    CRATE.loop = None
    print("monitor() exiting..")
    return

def add_monitor(ipaddress,user,password):
    alreadyrunning = False
    lmon = 0
    CRATE.lock.acquire()
    lmon = len(monitored)
    if ipaddress in monitored:
        alreadyrunning = True
    CRATE.lock.release()
    if alreadyrunning:
        CRATE.lock.acquire()
        for inst in CRATE.instances:
            if inst._state[0] == states.INIT:
                if CRATE.poweron:
                    inst._state = (states.ON,'')
                else:
                    inst._state = (states.OFF,'')

        CRATE.lock.release()
        return
    if lmon :
        raise Exception("Unsupported: multiple ip addresses")
    CRATE.loop = asyncio.new_event_loop()

    t = threading.Thread(target=monitor, args=(ipaddress,user,password,))
    t.start()
    power(True)
    return

def queue_request_delayed_setstate(rol,delay):
    time.sleep(delay)
    print(str(delay) + " seconds delayed")
    CRATE.lock.acquire()
    for inst in CRATE.instances:
        instrol = inst.rolisAlive()
        rv, msg =  HardLimits.checkmovelimitsandbugfix(instrol)
        if rv:
            inst._state  =(inst._state[0], msg +inst._state[1])
        rol.extend(instrol)
    CRATE.lock.release()
    queue_request(rol)
    time.sleep(1) # must yield before lock
    CRATE.lock.acquire()
    if CRATE.poweron:
        CRATE._state = (states.ON, "CONNECTED : "+CC2xlib.globals.CRATE.sessionid)
        print("Power is On")
    else:
        CRATE._state = (states.OFF, "CONNECTED : "+CC2xlib.globals.CRATE.sessionid)
        print("Power is Off")
    #for inst in CRATE.instances:
    #    inst._state = copy.deepcopy(CRATE._state)
    CRATE.lock.release()

def queue_request(rol):
    global  ctrlcreceived
    print("queue_request("+str(rol)+")")
    result = None
    if len(rol) == 0:
        return result
    if  ctrlcreceived:
        return result
    if not CRATE.loop:
        return result
    sid =''
    tmpstate = (states.UNKNOWN)
    while sid == '':
        CRATE.lock.acquire()
        tmpstate = copy.deepcopy(CRATE._state)
        sid = CRATE.sessionid[:]
        CRATE.lock.release()
        if states.FAULT in tmpstate :
            return result# no action
        if sid == '':
            time.sleep(1)
    future = asyncio.run_coroutine_threadsafe(execute_request(rol), CRATE.loop)
    timeout = 15
    try :
        result = future.result(timeout)
    except asyncio.TimeoutError:
        CRATE.lock.acquire()
        CRATE._state = (states.FAULT,'queue_request: The coroutine took too long, cancelling the task...')
        for inst in CRATE.instances:
            inst._state = copy.deepcopy(CRATE._state)
        print(CRATE._state[1])
        CRATE.lock.release()
        future.cancel()
    except Exception as exc:
        CRATE.lock.acquire()
        CRATE._state = (states.FAULT, f'The coroutine raised an exception: {exc!r}')
        for inst in CRATE.instances:
            inst._state = copy.deepcopy(CRATE._state)
        print(CRATE._state[1])
        CRATE.lock.release()
    return result

def cleanup():
    print("CC2x.cleanup()")

atexit.register(cleanup)
def signal_handler(sig, frame):
    global  ctrlcreceived
    ctrlcreceived = 1
    print('You pressed Ctrl+C! please wait up to 8s for exit')
    reset()
signal.signal(signal.SIGINT, signal_handler)
