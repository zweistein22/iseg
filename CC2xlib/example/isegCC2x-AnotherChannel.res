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
   {"Channel15": { "channels": ["0_1_1"], "operatingstate": "normal" }},
  ]
 }
"""
operatingstates = """
{
  "operatingstate":
  [ 
    {"normal": { "Control.voltageSet" : 15,
                 "Control.voltageRampspeedUp" : 5, 
                "Control.voltageRampspeedDown" :10,
                "Control.currentSet" : 1,
                "Setup.delayedTripTime" : 100 

     }}
   ]
}
"""

