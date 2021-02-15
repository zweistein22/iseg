["test/ERWIN-hvsupply/IntelligentPowersupply"]
type = "iseg.CC2x.IntelligentPowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
tripeventallmodulesoff = 0

transitions="""
{
"TRANSITION" :[
{"goOn":  [
              {"GROUP":["Window"],"Control.clearAll": [1]},
			  {"GROUP":["Anodes"],"Control.clearAll": [1,1,1]},
			  {"GROUP":["CathodeStripes"],"Control.clearAll": [1,1]},
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
              {"GROUP":["Anodes"],"Control.voltageSet": [1875,1900,1985]},
              {"GROUP":["Anodes"],"Status.ramping": [0,0,0] }
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
   {"Module0": { "CHANNEL": ["0_0"], "Control.on": 1, "Control.kill": 0, "Control.voltageRampspeed" : 0.17 }},
   {"Module1": { "CHANNEL": ["0_1"], "Control.on": 1,"Control.kill": 0, "Control.voltageRampspeed" : 0.17 }},
   {"Window": { "CHANNEL": ["0_1_7"], "OPERATINGSTYLE": "normal" }},
   {"Anodes": { "CHANNEL": ["0_1_0","0_1_1","0_1_2"]  ,"OPERATINGSTYLE": "normal" }},
   {"CathodeStripes": { "CHANNEL": ["0_1_4","0_1_5"],  "OPERATINGSTYLE": "slow" }}
 ]
}
"""
operatingstyles="""
{
  "OPERATNGSTYLE":
  [
    {"normal": {
	            "Control.clearAll" : 1 ,
                "Control.currentSet" : 1.0,
                "Setup.delayedTripTime" : 100,
				"Setup.delayedTripAction" : 2
     }},
	 {"slow": {
	            "Control.clearAll" : 1 ,
                "Control.currentSet" : 1.0,
                "Setup.delayedTripTime" : 100,
				"Setup.delayedTripAction" : 2
	 }}
   ]
}
"""


["test/ERWIN-hvsupply/Powersupply-Anode1"]
type = "iseg.isegCC2xChannel.PowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
channel = '0_0_0'

operatingstyle="""
{
    "Control.clearAll" : 1,
	"Control.currentSet" : 1.5,
    "Setup.delayedTripTime" : 1500,
	"Setup.delayedTripAction" : 2
}
"""

["test/ERWIN-hvsupply/Powersupply-Anode2"]
type = "iseg.isegCC2xChannel.PowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
channel = '0_0_1'

operatingstyle="""
{
    "Control.clearAll" : 1,
	"Control.currentSet" : 1.5,
    "Setup.delayedTripTime" : 1500,
	"Setup.delayedTripAction" : 2
}
"""

["test/ERWIN-hvsupply/Powersupply-Anode3"]
type = "iseg.isegCC2xChannel.PowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
channel = '0_0_2'

operatingstyle="""
{
    "Control.clearAll" : 1,
	"Control.currentSet" : 1.5,
    "Setup.delayedTripTime" : 1500,
	"Setup.delayedTripAction" : 2
}
"""

["test/ERWIN-hvsupply/Powersupply-CathodeStripe1"]
type = "iseg.isegCC2xChannel.PowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
channel = '0_0_4'

operatingstyle="""
{
    "Control.clearAll" : 1,
	"Control.currentSet" : 1.5,
    "Setup.delayedTripTime" : 1500,
	"Setup.delayedTripAction" : 2
}
"""

["test/ERWIN-hvsupply/Powersupply-CathodeStripe2"]
type = "iseg.isegCC2xChannel.PowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
channel = '0_0_5'

operatingstyle="""
{
    "Control.clearAll" : 1,
	"Control.currentSet" : 1.5,
    "Setup.delayedTripTime" : 1500,
	"Setup.delayedTripAction" : 2
}
"""


["test/ERWIN-hvsupply/Powersupply-Window"]
type = "iseg.isegCC2xChannel.PowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
channel = '0_0_7'

operatingstyle="""
{
    "Control.clearAll" : 1,
	"Control.currentSet" : 1.5,
    "Setup.delayedTripTime" : 1500,
	"Setup.delayedTripAction" : 2
}
"""


