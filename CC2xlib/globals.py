#  -*- coding: utf-8 -*-
#***************************************************************************
#* Copyright (C) 2020 by Andreas Langhoff *
#* <andreas.langhoff@frm2.tum.de> *
#* This program is free software; you can redistribute it and/or modify *
#* it under the terms of the GNU General Public License v3 as published *
#* by the Free Software Foundation; *
# **************************************************************************

import asyncio
import aiohttp
import websockets
import json
from urllib.request import urlopen
import time
from concurrent.futures import TimeoutError as ConnectionTimeoutError
import base64
import os
import inspect
from os.path import expanduser

import entangle.device.iseg.CC2xlib.json_data as json_data
import entangle.device.iseg.CC2xlib.ping as ping

sessionid = ''
websocket = None

channelfolders = []




async def heartbeat(connection):
    while True:
            try:
                await connection.send('ping')
                await asyncio.sleep(15)
            except websockets.exceptions.ConnectionClosed:
                print('Connection with server closed')
                break
    
async def listen(connection):
    global sessionid
    while True:
        try :
            response = await connection.recv()
            
            dict = json.loads(response)
            print(dict)
            if "trigger" in dict:
                if dict["trigger"] == "false":
                    continue
                   
            if "d" in dict:
                data  = dict["d"]
                if "file" in dict:
                    filename = dict["file"]
                    bytes = base64.b64decode(data)
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
                        file.write(bytes)
                        print(fullpath)

            if "i" in dict:
                if  dict["i"] == sessionid:
                     # our sessionid, so
                     print(dict)
                     
                     # fill out our log with the results
        except Exception as inst:
            print(type(inst))    # the exception instance
            print(inst.args)     # arguments stored in .args
            print(inst)          # __str__ allows args to be printed directly,
            break
    


async def login(address,user,password):
    timeout = 5
    global websocket
    global sessionid
    try:
        websocket = await asyncio.wait_for(websockets.connect('ws://'+address+':8080'), timeout)
        cmd = json_data.login(user,password)
        await websocket.send(cmd)
        response = await websocket.recv()
        dict = json.loads(response)
        sessionid = dict["i"]
        
    except  ConnectionTimeoutError as e:
        print("Connection timeout")
        websocket = None
   

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

async def getConfig(sessionid):
        global websocket
 #   async with websockets.connect('ws://'+address+':8080') as websocket:
        cmd = json_data.getConfig(sessionid)
        await websocket.send(cmd)
               

async def execute_request(sessionid, requestobjlist):
        global websocket
        #async with websockets.connect('ws://'+address+':8080') as websocket:
        cmd = json_data.request(sessionid, requestobjlist)
        await websocket.send(cmd)
        
       
monitored = []

def monitor(address,user,password,loop):
    asyncio.set_event_loop(loop)
    #ping.ping(address)
    loop.run_until_complete(login(address,user,password))
    monitored.append(address)
    
    loop.run_until_complete(getItemsInfo(address))
    loop.run_until_complete(getConfig(sessionid))

    future1 = asyncio.ensure_future(heartbeat(websocket))
    future2 = asyncio.ensure_future(listen(websocket))
    loop.run_until_complete(asyncio.gather(future1,future2))
    
    monitored.remove(address)

loop = None
def add_monitor(ipaddress,user,password):
    global loop
    if ipaddress in monitored:
        return
    if len(monitored) :
        raise Exception("Unsupported: multiple ip addresses")
    loop = asyncio.get_event_loop()
    import threading
    t = threading.Thread(target=monitor, args=(ipaddress,user,password,loop,))
    t.start()


def queue_request(rol):
    if len(rol) == 0: return
    #loop.call_soon_threadsafe(execute_request(sessionid, rol))
    loop.run_until_complete(execute_request(sessionid, rol))