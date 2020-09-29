["test/Erwin/HV-Powersupply"]
type = "iseg.CC2x.PowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0


transitions="""
{
"TRANSITION" :[
{"Off->On":  [
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
{"On->Off":  [
             {"GROUP":["Anodes"],"Control.on": [0,0,0] } ,
             {"GROUP":["Anodes"],"Status.ramping": [0,0,0] },
             {"GROUP":["CathodeStripes"],"Control.on": [0,0]},
             {"GROUP":["Window"],"Control.on": [0] },
             {"GROUP":["Window"],"Status.ramping": [0] },
             {"GROUP":["CathodeStripes"],"Status.ramping": [0, 0]}
            ]
},
{"On->Moving":  [
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
   {"Module0": { "CHANNEL": ["0_0"], "Control.kill": 0, "Control.voltageRampspeed" : 0.1 }},
   {"Module1": { "CHANNEL": ["0_1"], "Control.kill": 0, "Control.voltageRampspeed" : 0.2 }},
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
                "Control.currentSet" : 2,
                "Setup.delayedTripTime" : 102 
     }},
	 {"slow": {    
                    "Control.currentSet" : 3,
                    "Setup.delayedTripTime" : 111
	 }}
   ]
}
"""

