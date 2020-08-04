import json

def make_requestobject(command,line,address,channel,itemtype):
    reqobj = {}
    reqobj["c"] = command
    reqobj["p"] = {
        "p": {
            "l": line, 
		    "a": address,
			"c": channel
		},
		"i": itemtype,
		"v": "",
		"u": ""
    }

    return reqobj


def checkResponse(_dict):
    if "trigger" in _dict.keys():
        if _dict["trigger"] != "true":
            raise Exception('trigger', 'not acknolwdged')
    if "t" in _dict.keys():
        struc_type = _dict["t"]
        print(struc_type )
        if struc_type == "info":
            print(struc_type["info"])
            pass
      


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


