#  -*- coding: utf-8 -*-
#***************************************************************************
#* Copyright (C) 2020 by Andreas Langhoff *
#* <andreas.langhoff@frm2.tum.de> *
#* This program is free software; you can redistribute it and/or modify *
#* it under the terms of the GNU General Public License v3 as published *
#* by the Free Software Foundation; *
# **************************************************************************

class HardLimits:
    unitTime = 'ms'
    unitCurrent = 'uA'
    maxTripCurrent = 10
    maxVoltage = 90
    tripEventAllModulesOff = False


    @staticmethod
    def checkmovelimitsandbugfix(rol):
        cmds = ["Control.voltageSet","Control.currentSet","Setup.delayedTripTime"]
        limits = [HardLimits.maxVoltage, HardLimits.maxTripCurrent,0]
        units = ['',HardLimits.unitCurrent,HardLimits.unitTime]
        #units is a bug fix for iges ics
        limitsmoved = 0
        wheremoved = ''
        for ro in rol:
            if ro['c'] == "setItem":
                item = ro['p']
                if not 'i' in item:
                    continue
                ourcmd = item['i']
                if ourcmd in cmds:
                    i = cmds.index( ourcmd)
                    v = float(item['v'])
                    sign = 1
                    if v < 0:
                        sign = -1
                    if limits[i]:
                        if abs(v) > limits[i]:
                            item['v'] = str(sign * limits[i])
                            limitsmoved = 1
                            wheremoved = wheremoved + ", " + ourcmd  + " CHANGED:" + str(item['v'])
                    if units[i]:
                        item['u'] = units[i]

        return (limitsmoved,wheremoved)

print("HardLimits.unitTime="+str(HardLimits.unitTime))
print("HardLimits.unitCurrent="+str(HardLimits.unitCurrent))
print("HardLimits.maxTripCurrent="+str(HardLimits.maxTripCurrent))
print("HardLimits.maxVoltage="+str(HardLimits.maxVoltage))
