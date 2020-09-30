["test/Erwin/HV-Powersupply"]
type = "iseg.CC2x.PowerSupply"

address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0

groups ="""
{
 "group": [
   {"Module0": { "CHANNEL": ["0_0"], "Control.kill": 0 }},
   {"Channel1": { "channels": ["0_0_0"], "operatingstate": "normal" }},
  ]
 }
"""
operatingstates = """
{
  "operatingstate":
  [ 
    {"normal": { "Control.voltageSet" : 2200,
                 "Control.voltageRampspeedUp" : 5, 
                "Control.voltageRampspeedDown" :10,
                "Control.currentSet" : 2,
                "Setup.delayedTripTime" : 100 

     }}
   ]
}
"""

