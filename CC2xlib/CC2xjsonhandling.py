import json
from typing import List


def isSingleChannel(lac:str)->bool:
    s = lac.split("_")
    if len(s) > 2:
        return True
    return False

def isModuleAddress(lac:str)->bool:
    s = lac.split("_")
    if len(s) > 2:
        return False
    if len(s) > 1:
        return True
    return False


def getTransitions(transitions:str)->List[str]:
    jobjtransitions = json.loads(transitions)
    if 'TRANSITION' in jobjtransitions:
        return jobjtransitions['TRANSITION']
    return []

def getTransitionNames(transitions:str)->List[str]:
    rv = []
    if not transitions:
        return rv
    tr = getTransitions(transitions)
    for t in tr:
        for name in t:
            rv.append(name)
    return rv

def getStatusValue(channel:str, item:str, statusjsonstr:str):
    s_all = json.loads(statusjsonstr)
    for it in s_all:
        if it==channel:
            objects = s_all[channel]
            for cmd in objects:
                if cmd == item:
                    vu = objects[cmd]
                    return vu['v']
    return None

def getGroupNames(groups:str)->List[str]:
    rv = []
    jobjgroups = json.loads(groups)
    if 'GROUP' in jobjgroups:
        groups = jobjgroups['GROUP']
        for group in groups:
            # pylint: disable=unused-variable
            for key, val in group.items():
            #must keep val , otherwise different assignment to key, pylint will report a warning -> dead wrong
                rv.append(key)
    return rv

def getChannels(groups:str, groupname:str)->List[str]:
    rv = []
    jobjgroups = json.loads(groups)
    if 'GROUP' in jobjgroups:
        ggroups = jobjgroups['GROUP']

        for group in ggroups:
            for key,val in group.items():
            #must keep val , otherwise different assignment to key, pylint will report a warning -> dead wrong
                if key == groupname:
                    channels = val["CHANNEL"]
                    for ch in channels:
                        rv.append(ch)
    return rv

def getOperatingStyleNames(operatingstyles:str)->List[str]:
    rv = []
    if not operatingstyles:
        return rv
    jobjoperatingstyles = json.loads(operatingstyles)
    if not jobjoperatingstyles:
        return rv
    if 'OPERATNGSTYLE' in jobjoperatingstyles:
        groups = jobjoperatingstyles['OPERATNGSTYLE']
        for group in groups:
            # pylint: disable=unused-variable
            for key,val in group.items():
             #must keep val , otherwise different assignment to key, pylint will report a warning -> dead wrong
                rv.append(key)
    return rv
