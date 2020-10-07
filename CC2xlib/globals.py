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
import asyncio
import aiohttp
import websockets
import json
import time
from concurrent.futures import TimeoutError as ConnectionTimeoutError
import base64
import os
import inspect
from os.path import expanduser

from entangle.core import states
import threading

from entangle.device.iseg import CC2xlib
from entangle.device.iseg.CC2xlib import json_data
 

instances = []

always_monitored = ['0_1000_','__']

lock = threading.Lock()
last_reqobj = ''
sessionid = ''
websocket = None
itemUpdated = {}
_state = (states.UNKNOWN)
poweron = False

loop = None

def StatusJson(channellist)->str:
    rv = ''
    tmp = {}
    lock.acquire()
    for ch in channellist:
        if ch in itemUpdated:
            tmp[ch] = itemUpdated[ch]
    rv = json.dumps(tmp)
    lock.release()
    return rv

ctrlcreceived = 0

async def heartbeat(connection):
    global _state, sessionid, last_reqobj
    while True:
        try:
            await asyncio.sleep(8)
            rol = []
            lock.acquire()
            rol.append(json_data.make_requestobject("getUpdate", always_monitored[0],''))
            r = json_data.request(sessionid,rol)
            last_reqobj = r
            lock.release()
            print("heartbeat!!!")
            await connection.send(r)
        except websockets.exceptions.ConnectionClosed:
            _state = (states.FAULT, 'Connection with server closed.')
            print(_state[1])
            break
        except Exception as inst:
            print("heartbeat")
            print(type(inst))    # the exception instance
            print(inst.args)     # arguments stored in .args
            print(inst)  
            break
    return

v_measure_received = 0    
async def listen(connection):
    global sessionid,lock,itemUpdated,websocket,always_monitored,instances,poweron,last_reqobj
    global v_measure_received
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
                        lock.acquire()
                        print(last_reqobj)
                        lock.release()
                        print("RESPONSE\r\n")
                        print(dictlist)
                        print("\r\n")

                if "t" in adict:
                    #if adict["t"] == "info":
                        #print(adict)
                        
                    #if adict["t"] == "response":
                    #    print(adict)
                        
                    if "c" in adict:
                        contentlist = adict["c"]
                        #print("contentlist len="+str(len(contentlist)))
                        for c in contentlist:
                            lac = CC2xlib.json_data.getshortlac(c["d"]["p"])
                            timestamp = c["d"]["t"]
                            someinstancesubscribed = 0
                            lock.acquire()
                            for inst in instances:
                                if lac in  inst.channels_handled:
                                    someinstancesubscribed = 1
                            lock.release()
                            if (someinstancesubscribed or (lac in always_monitored)):
                                command = c["d"]["i"]
                                if not ( command in ["Status.voltageTerminalMeasure","Status.currentMeasure","Status.heartBeat","System.time","Status.temperature0","Status.temperature1"]): #,"Status.voltageMeasure"]):
                                    if command == "Status.voltageMeasure":
                                        v_measure_received = v_measure_received + 1
                                        if not (v_measure_received % 5) :
                                            print(c["d"])
                                    else:
                                        print(c["d"])
                                


                                if command in ["Status.inputError"]:
                                    print("\r\n")
                                    print("REQUEST\r\n")
                                    lock.acquire()
                                    print(last_reqobj)
                                    lock.release()
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

                                if (value and command in ["Error.currentLimitExceeded", "Status.currentTrip", "Status.arc", "Event.arc", "Error.arc"]):
                                    lock.acquire()
                                    _state = (states.FAULT,lac + ":"+ command)
                                    for inst in instances:
                                        inst._state = _state
                                        print(_state[1])
                                    lock.release()

                                if lac == always_monitored[1]:
                                    maxconnections = 2
                                    #NOT SURE : BUG in iseg module, will report disconnected clients only with a delay
                                    #doing several Reset() within short time the number of connected clients will temporarily increase
                                    if (command == "Status.connectedClients" and int(value) > maxconnections):
                                        print("only "+str(maxconnections)+ " client(s) connection allowed.")
                                        await logout()
                                        await connection.close()
                                        break
                                
                                ourdict = {}
                                lock.acquire()
                                if lac in itemUpdated:
                                    ourdict = itemUpdated[lac]
                                # this is a dict again, and that we will update
                                ourdict[command] = vu
                                itemUpdated[lac] = ourdict
                                lock.release()

                                if lac == always_monitored[0]:
                                    if command == "Status.power":
                                        lock.acquire()
                                        if  value == '0':
                                            poweron = False
                                            _state = (states.OFF,command)
                                        else :
                                            poweron = True
                                            _state = (states.ON,command)
                                        for inst in instances:
                                            inst._state = _state
                                        if poweron :
                                            print("Power is On")
                                        else:
                                            print("Power is Off")
                                        lock.release()
                                    continue
                                lock.acquire()
                                for inst in instances:
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
                                                if ch in itemUpdated:
                                                    od2 = itemUpdated[ch]
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
                                                        except:
                                                            allrequestedok = False
                                                    else :
                                                        allrequestedok = False
                                                        
                                                else :
                                                    allrequestedok = False
                                                    
                                                k = k + 1

                                        if not poweron:
                                            inst._state = (inst._state[0],"CANCELLED:"+inst.waitstring)
                                            print(inst._state[1])
                                            inst.waitstring = ''
                                            inst.waitstringmintime = ''

                                        if allrequestedok:
                                            inst._state = (inst._state[0],"FINISHED:"+inst.waitstring)
                                            print(inst._state[1])
                                            inst.waitstring = ''
                                            inst.waitstringmintime = ''
                                lock.release()

                                



                  # fill out our log with the results
        except Exception as inst:
            print(type(inst))    # the exception instance
            print(inst.args)     # arguments stored in .args
            print(inst)          # __str__ allows args to be printed directly,
            break
   
    lock.acquire()
    websocket = None
    lock.release() 

async def logout():
    global websocket
    global sessionid
    
    try:
        wsok = 1
        lock.acquire()
        if not websocket:
            wsok = 0
        lock.release()
        if not wsok:
            return
        cmd = CC2xlib.json_data.logout(sessionid)
        await websocket.send(cmd)
        await websocket.close()
        websocket = None
    except:
        pass
    if poweron:
        _state =(states.ON,"DISCONNECTED")
    else:
        _state =(states.OFF,"DISCONNECTED")
    print(_state)

async def login(address,user,password):
    timeout = 5
    global websocket
    global sessionid
    global _state,poweron, ctrlcreceived
    try:
        websocket = await asyncio.wait_for(websockets.connect('ws://'+address+':8080'), timeout)
        cmd = CC2xlib.json_data.login(user,password)
        await websocket.send(cmd)
        response = await websocket.recv()
        if ctrlcreceived:
            return
        adict = json.loads(response)
        lock.acquire()
        sessionid = adict["i"]
        if poweron:
            _state =(states.ON,"CONNECTED : "+sessionid)
        else :
            _state =(states.OFF,"CONNECTED : "+sessionid)
        print(_state)
        for inst in instances:
            inst._state = _state
        lock.release()
       
        
    except  ConnectionTimeoutError:
        lock.acquire()
        websocket = None
        _state = (states.FAULT,"Connection timeout")
        print(_state[1])
        lock.release()
   

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
    global websocket, sessionid
    cmd = CC2xlib.json_data.getConfig(sessionid)
    await websocket.send(cmd)
               

async def execute_request(requestobjlist):
    global websocket, sessionid, last_reqobj
    cmd = CC2xlib.json_data.request(sessionid, requestobjlist)
    lock.acquire()
    last_reqobj = cmd
    lock.release()
    await websocket.send(cmd)
    return True
        

monitored = []

future1 = None
future2 = None

def reset():
    global future1,future2, loop, itemUpdated, websocket, _state
    if _state == states.UNKNOWN:
        return
    if websocket and loop:
        future = asyncio.run_coroutine_threadsafe(logout(), loop)
        timeout = 3
        try :
            result = future.result(timeout)
            if result:
                print(result)
            print("logout call done")
        except asyncio.TimeoutError:
            lock.acquire()
            _state = (states.FAULT,'The logout() coroutine call too long, cancelling the task...')
            
            for inst in instances:
                inst._state = _state
            print(_state[1])
            lock.release()
            future.cancel()
        except Exception as exc:
            lock.acquire()
            _state = (states.FAULT, f'The coroutine raised an exception: {exc!r}')
            for inst in instances:
                inst._state = _state
            print(_state[1])
            lock.release()

    if not (future1 and future2):
        if loop:
            loop.close()
        loop = None
    if future1:
        loop.call_soon_threadsafe(future1.cancel)
        
    if future2:
        loop.call_soon_threadsafe(future2.cancel)
    
    
    while loop:
        time.sleep(1)
    websocket = None
    print("reset end")
    _state = (states.UNKNOWN)
    

def power(value: bool) -> None:
    rol = []
    rol.append( CC2xlib.json_data.make_requestobject("setItem",always_monitored[0],"Control.power",str(int(value))))
    queue_request(rol)

def monitor(address,user,password):
    global websocket, _state, loop, future1, future2, monitored, sessionid
    asyncio.set_event_loop(loop)
    #ping.ping(address)
    loop.run_until_complete(login(address,user,password))
    tmpstate = (states.UNKNOWN)
    lock.acquire()
    tmpstate = _state
    lock.release()
    connected = False
    for st in tmpstate:
        if st.startswith('CONNECTED'):
            connected = True
   
    if not connected:
        return
    lock.acquire()
    monitored.append(address)
    lock.release()
    loop.run_until_complete(getItemsInfo(address))
    loop.run_until_complete(getConfig())
    try :
        future1 = asyncio.ensure_future(heartbeat(websocket))
        future2 = asyncio.ensure_future(listen(websocket))
        loop.run_until_complete(asyncio.gather(future1,future2))
        
        
    except:
        pass
    loop.run_until_complete(logout())
    lock.acquire()
    monitored.remove(address)
    #monitored = []
    #itemUpdated = {}
    sessionid = ''
    lock.release()
    future1 = None
    future2 = None
    loop = None
    print("monitor() exiting..")
   



def add_monitor(ipaddress,user,password):
    global loop,instances
    alreadyrunning = False
    lmon = 0
    lock.acquire()
    lmon = len(monitored)
    if ipaddress in monitored:
        alreadyrunning = True
    lock.release()
    if alreadyrunning: 
        lock.acquire()
        for inst in instances:
            if inst._state[0] == states.INIT:
                if poweron:
                    inst._state = (states.ON,'')
                else:
                    inst._state = (states.OFF,'')

        lock.release()
        return
    if lmon :
        raise Exception("Unsupported: multiple ip addresses")
    loop = asyncio.new_event_loop()
    
    t = threading.Thread(target=monitor, args=(ipaddress,user,password,))
    t.start()
    power(True)



   

def queue_request(rol):
    global sessionid, _state, loop, instances, ctrlcreceived
    if len(rol) == 0: return
    if  ctrlcreceived:
        return
    if not loop:
        return
    sid =''
    tmpstate = (states.UNKNOWN)
    while sid == '':
        lock.acquire()
        tmpstate = _state
        sid = sessionid[:]
        lock.release()
        if states.FAULT in tmpstate :
            return # no action
        if sid == '':
            time.sleep(1)
    
    future = asyncio.run_coroutine_threadsafe(execute_request(rol), loop)
    timeout = 15
    try :
        result = future.result(timeout)
    except asyncio.TimeoutError:
        lock.acquire()
        _state = (states.FAULT,'The coroutine took too long, cancelling the task...')
        for inst in instances:
            inst._state = _state
        print(_state[1])
        lock.release()
        future.cancel()
    except Exception as exc:
        lock.acquire()
        _state = (states.FAULT, f'The coroutine raised an exception: {exc!r}')
        for inst in instances:
            inst._state = _state
        print(_state[1])
        lock.release()
       
    else:
        return result

def cleanup():
    print("CC2x.cleanup()")
    




atexit.register(cleanup)


    
def signal_handler(sig, frame):
    global loop, ctrlcreceived

    ctrlcreceived = 1
    print('You pressed Ctrl+C! please wait up to 8s for exit')
    reset()

    

signal.signal(signal.SIGINT, signal_handler)
   
    