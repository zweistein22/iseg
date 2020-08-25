
import json_data
import declxml
from xml.etree import cElementTree as ElementTree

#tree = ElementTree.parse('icsConfig.xml')
#root = tree.getroot()
#cfs = root.findall('./channelFolders/channelFolder')

#folders = []
#for child in cfs:
#    folders.append(child)

import toml

with open('entangle/example/Charm-small-HV-supply.res') as fd:
    data = toml.load(fd)
    rampstyles = data["test/Erwin/small-detector/HV-Supply"]["rampstyles"]
    groups = data["test/Erwin/small-detector/HV-Supply"]["groups"]
    sequences = data["test/Erwin/small-detector/HV-Supply"]["sequences"]

    execsequence = "on"
    rol = []
    for seq in sequences:
        seqname = list(seq.keys())[0]
        if seqname == execsequence :
            for step in seq[seqname] :
                for group in groups:
                    groupname = list(group.keys())[0]
                    if step == groupname:
                        channels = group[groupname]['channels']
                        rampstyle = group[groupname]['rampstyle']
                        for rstyle in rampstyles:
                            stylename = list(rstyle.keys())[0]
                            if stylename == rampstyle :
                               for k, v in rstyle[stylename].items():
                                    item = k.replace("_",".")
                                    for channel in channels :
                                          rol.append(json_data.make_requestobject("setItem",channel,item,v))



    currentstyle = "steep"

    for rstyle in rampstyles:
        stylename = list(rstyle.keys())[0]
        if stylename == currentstyle :
             print(stylename)
             for k, v in rstyle[stylename].items():
                 print(k)
                 print(v)
                 item = k.replace("_",".")
    
import xmltodict
folders = {}
with open('icsConfig.xml') as fd:
    ics = xmltodict.parse(fd.read())
    folders =  ics['icsConfig']['channelFolders']

for cf in folders['channelFolder']:
    for k,v in cf.items():
        print(k)
        print(v)

