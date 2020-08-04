#!/usr/bin/env python

import asyncio
import aiohttp
import websockets
import json_data
import ping
from urllib.request import urlopen
import time
from concurrent.futures import TimeoutError as ConnectionTimeoutError

address = '192.168.1.1'
user = 'admin'
password = 'password'
sessionid = ''

async def login():
    timeout = 5
    try:
        websocket = await asyncio.wait_for(websockets.connect('ws://'+address+':8080'), timeout)
        cmd = json_data.login(user,password)
        await websocket.send(cmd)
        sessionid = await websocket.recv()
        print(sessionid)
    except  ConnectionTimeoutError as e:
        print(e)
   

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

async def getConfig(session):
     async with websockets.connect('ws://'+address+':8080') as websocket:
        cmd = json_data.getConfig(session)
        await websocket.send(cmd)
        icJson = await websocket.recv()
        print(icJson)

#ping.ping(address)
loop = asyncio.get_event_loop()
loop.run_until_complete(login())
#loop.run_until_complete(getItemsInfo())
loop.run_until_complete(getConfig(sessionid))

loop.close()
