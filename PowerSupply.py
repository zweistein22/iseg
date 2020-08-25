#!/usr/bin/env python
#                           _              _                _
#	___  __ __ __  ___     (_)     ___    | |_     ___     (_)    _ _
#   |_ /  \ V  V / / -_)    | |    (_-<    |  _|   / -_)    | |   | ' \
#  _/__|   \_/\_/  \___|   _|_|_   /__/_   _\__|   \___|   _|_|_  |_||_|
#	   .
#	   |\       Copyright (C) 2020 by Andreas Langhoff
#	 _/]_\_                            <andreas.langhoff@frm2.tum.de>
# ~~~"~~~~~^~~   This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License v3
# as published by the Free Software Foundation;

import time

from entangle import base
from entangle.core import ALARM, BUSY, FAULT, ON, Prop, intrange, subdev
from entangle.core.errors import CommunicationFailure, ConfigurationError, \
    InvalidOperation, InvalidValue, UnrecognizedHardware


class PowerSupply(base.PowerSupply):
    """Controls an Iseg CC2x  high-voltage power supply via websocket."""

    properties = {
        'iodev':    Prop(subdev, 'I/O device name.'),
        'blockedspeeds': Prop(pairsof(int), 'Array of blocked speed ranges: '
                              'min1, max1, min2, max2, ...', default=[]),
        'protocol': Prop(oneof('text', 'pseudoxml'), 'Protocol to use.'),
        'sysname':  Prop(nonemptystring, '"Sysname" string for the '
                         'pseudoxml protocol.', default=''),
        'systype':  Prop(nonemptystring, '"Systype" string for the '
                         'pseudoxml protocol.', default='NVS'),
        'sysnum':   Prop(int, '"Sysnum" for the pseudoxml protocol.',
                         default=0),
        'precision': Prop(int, 'delta between requested rpm in labview '
                          'software', default=10),
    }




