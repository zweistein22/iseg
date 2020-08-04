import json


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


