["test/Erwin/small-detector/HV-Supply"]
type = "ISEGCC2x.PowerSupply"
address = '192.168.1.1'
user = 'admin'
password = 'password'
rampstyles = [ 
    {normal = {Control_voltageRampspeedUp = 5, Control_voltageRampspeedDown = 10, Control_voltageSet = 2200, Control_currentSet = 1,Setup_delayedTripTime =100 }},
    {steep = {Control_voltageRampspeedUp = 15, Control_voltageRampspeedDown = 30, Control_voltageSet = 2200, Control_currentSet = 1,Setup_delayedTripTime =100 }},
]

groups = [
    {entrancewindow = {channels = ["0_0_0", "0_0_1"], rampstyle = "normal" }},
    {anodewires = {channels = ["0_0_2", "0_0_3"], rampstyle ="normal" }},
    {cathodestripes = {channels = ["0_0_4"], rampstyle = "normal" }},
]

sequences = [
    {on = ["entrancewindow","anodewires","cathodestripes"]},
    {off = ["cathodestripes","anodewires","entrancewindow"]},
]


