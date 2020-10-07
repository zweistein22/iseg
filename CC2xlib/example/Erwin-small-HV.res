["test/Erwin/HV-Powersupply"]
type = "iseg.CC2x.IntelligentPowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
unitTime = 'ms'
unitCurrent ='µA'
maxTripCurrent = 2
maxVoltage = 2200


transitions="""
{
"TRANSITION" :[
{"goOn":  [
              {"GROUP":["Window"],"Control.voltageSet": [-1000]},
              {"GROUP":["Window"],"Control.on": [1] },
              {"GROUP":["Window"],"Status.ramping": [0] },
              {"GROUP":["Anodes"],"Control.voltageSet": [2075,2100,2085]},
              {"GROUP":["Anodes"],"Control.on": [1,1,1] },
              {"GROUP":["CathodeStripes"],"Control.voltageSet": [75,80]},
              {"GROUP":["CathodeStripes"],"Control.on": [1,1]},
              {"GROUP":["CathodeStripes"],"Status.ramping": [0,0]},
              {"GROUP":["Anodes"],"Status.ramping": [0,0,0] }
             ]
},
{"goOff":  [
             {"GROUP":["Anodes"],"Control.on": [0,0,0] } ,
             {"GROUP":["Anodes"],"Status.ramping": [0,0,0] },
             {"GROUP":["CathodeStripes"],"Control.on": [0,0]},
             {"GROUP":["Window"],"Control.on": [0] },
             {"GROUP":["Window"],"Status.ramping": [0] },
             {"GROUP":["CathodeStripes"],"Status.ramping": [0, 0]}
            ]
},
{"goMoving":  [
              {"GROUP":["Anodes"],"Control.voltageSet": [1200,1220,1230]},
              {"GROUP":["Anodes"],"Status.ramping": [0,0,0] }
             ]
}
]
}
"""

groups="""
{
 "GROUP": [
   {"Module0": { "CHANNEL": ["0_0"], "Control.kill": 0 , "Control.voltageRampspeed" : 0.18 }},
   {"Module1": { "CHANNEL": ["0_1"], "Control.kill": 0 , "Control.voltageRampspeed" : 0.19 }},
   {"Anodes": { "CHANNEL": ["0_0_0","0_0_1","0_0_2"]  ,"OPERATINGSTYLE": "normal" }},
   {"CathodeStripes": { "CHANNEL": ["0_0_4","0_0_5"],  "OPERATINGSTYLE": "slow" }},
   {"Window": { "CHANNEL": ["0_0_7"], "OPERATINGSTYLE": "normal" }}
 ]
}
"""

operatingstyles="""
{
  "OPERATNGSTYLE":
  [ 
    {"normal": {
                "Control.currentSet" : 0.5,
                "Setup.delayedTripTime" : 51,
                "Setup.delayedTripAction": 2
     }},
	 {"slow": {    
                    "Control.currentSet" : 1,
                    "Setup.delayedTripTime" : 103,
                    "Setup.delayedTripAction": 2
	 }}
   ]
}
"""