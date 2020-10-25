["test/Erwin/HV-Powersupply-ModulesSetting"]
type = "iseg.CC2x.IntelligentPowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
transitions = ''
operatingstyles = ''

groups="""
{
 "GROUP": [
   {"Module0": { "CHANNEL": ["0_0"], "Control.kill": 0, "Control.voltageRampspeed" : 0.167 }},
   {"Module1": { "CHANNEL": ["0_1"], "Control.kill": 0, "Control.voltageRampspeed" : 0.167 }}
 ]
}
"""

#Control.voltageRampspeed is in % of Nominal Voltage (is 3000V with current device)


["test/Erwin/HV-Powersupply-ChannelLeftTop"]
type = "iseg.isegCC2xChannel.PowerSupply"
address = '172.25.25.56'
user = 'admin'
password = 'password'
absmin = 0
absmax = 0
channel = '0_0_0'
operatingstyle="""
{
    "Control.currentSet" : 1.0,
    "Setup.delayedTripTime" : 500,
	"Setup.delayedTripAction" : 2
}
"""