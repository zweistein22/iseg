#!/usr/bin/env python

import asyncio
import aiohttp
import websockets
import json
import json_data
import ping
from urllib.request import urlopen
import time
from concurrent.futures import TimeoutError as ConnectionTimeoutError
import base64

address = '192.168.1.1'
user = 'admin'
password = 'password'
sessionid = ''
websocket = None

channelfolders = []

async def login():
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

async def heartbeat(url: str, period: float) -> None:
    async with aiohttp.ClientSession() as session:
        while True:
            await session.put(url)
            await asyncio.sleep(period)

async def getItemsInfo():
    async with aiohttp.ClientSession() as session:
        url = 'http://'+address+'/api/getItemsInfo'
        html = await fetch(session, url)
        with open("getItemsInfo.xml", "wb") as file:
            file.write(html)

async def getConfig(sessionid):
        global websocket
 #   async with websockets.connect('ws://'+address+':8080') as websocket:
        cmd = json_data.getConfig(sessionid)
        await websocket.send(cmd)
        response = await websocket.recv()
        dict = json.loads(response)
        data  = dict["d"]
        filename = dict["file"]
        bytes = base64.b64decode(data)
        with open(filename, "wb") as file:
            file.write(bytes)

async def execute_request(sessionid, requestobjlist):
        global websocket
    #async with websockets.connect('ws://'+address+':8080') as websocket:
        cmd = json_data.request(sessionid, requestobjlist)
        await websocket.send(cmd)
        response = await websocket.recv()
        dict = json.loads(response)
        json_data.checkResponse(dict)
       
#ping.ping(address)
loop = asyncio.get_event_loop()
loop.run_until_complete(login())
#loop.run_until_complete(getItemsInfo())
loop.run_until_complete(getConfig(sessionid))

rol = [] # request object list 
rol.append(json_data.make_requestobject("getItem","0_0_0","Control.voltageSet"))

loop.run_until_complete(execute_request(sessionid,rol))

loop.close()
