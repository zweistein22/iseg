#  -*- coding: utf-8 -*-
#***************************************************************************
#* Copyright (C) 2020 by Andreas Langhoff *
#* <andreas.langhoff@frm2.tum.de> *
#* This program is free software; you can redistribute it and/or modify *
#* it under the terms of the GNU General Public License v3 as published *
#* by the Free Software Foundation; *
# **************************************************************************


import json

def make_requestobject(command,lac,itemtype,val="",unit=""):
    s = lac.split("_")
    line = int(s[0])
    address = int(s[1])
    channel = int(s[2])
    reqobj = {}
    reqobj["c"] = command
    reqobj["p"] = {
        "p": {
            "l": line, 
		    "a": address,
			"c": channel
		},
		"i": itemtype,
		"v": val,
		"u": unit
    }

    return reqobj


def checkResponse(_dict):
    for d in _dict:
        if "trigger" in d:
            if d["trigger"] != "true":
                raise Exception('trigger', 'not acknolwdged')
      


def login(username,password):
    data = {}
    data['i'] = ''
    data['t'] = 'login'
    data['c'] = {"l":username ,"p":password, "t":""}
    data['r'] = "websocket"
    return json.dumps(data)

def logout(sessionid):
    data = {}
    data['i'] = sessionid
    data['t'] = 'logout'
    data['c'] = {}
    data['r'] = "websocket"
    return json.dumps(data)

def getConfig(sessionid):
    data = {}
    data['i'] = sessionid
    data['t'] = 'getConfig'
    data['c'] = []
    data['r'] = "websocket"
    return json.dumps(data)

def setConfig(sessionid,base64encodedxml):
    data = {}
    data['i'] = sessionid
    data['t'] = 'setConfig'
    data['f'] = 'iCSConfig.xml'
    data['c'] = []
    data['d'] = base64encodedxml
    data['r'] = "websocket"
    return json.dumps(data)

def request(sessionid,requestpacketobjects):
    data = {}
    data['i'] = sessionid
    data['t'] = 'request'
    data['c'] = requestpacketobjects
    data['r'] = "websocket"
    return json.dumps(data)


