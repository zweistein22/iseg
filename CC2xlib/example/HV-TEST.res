["test/Erwin/HV-IntelligentPowersupply"]
type = "iseg.CC2x.IntelligentPowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
tripeventallmodulesoff = 1

transitions="""
{
"TRANSITION" :[
{"goOn":  [
              {"GROUP":["Window"],"Control.voltageSet": [-80]},
              {"GROUP":["Window"],"Control.on": [1] },
              {"GROUP":["Window"],"Status.ramping": [0] }
             ]
},
{"goOff":  [
             {"GROUP":["Window"],"Control.on": [0] },
             {"GROUP":["Window"],"Status.ramping": [0] }
            ]
}
]
}
"""
#Control.voltageRampspeed is in % of Nominal Voltage (is 3000V with current device)
# so 0.1666 is 5V/s

groups="""
{
 "GROUP": [
   {"Module0": { "CHANNEL": ["0_0"], "Control.kill": 0 , "Control.voltageRampspeed" : 0.18 }},
   {"Module1": { "CHANNEL": ["0_1"], "Control.kill": 0 , "Control.voltageRampspeed" : 0.19 }},
   {"Window": { "CHANNEL": ["0_0_7"], "OPERATINGSTYLE": "normal" }}
 ]
}
"""

operatingstyles="""
{
  "OPERATNGSTYLE":
  [
    {"normal": {
                "Control.clearAll" : 1 ,
                "Control.currentSet" : 1.5,
                "Setup.delayedTripTime" : 500,
                "Setup.delayedTripAction": 2
     }}
   ]
}
"""