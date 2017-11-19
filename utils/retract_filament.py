#!/usr/bin/env python3
from __future__ import print_function

import os
import sys
from time import sleep

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from uf.utils.log import logger_init, logging
from uf.wrapper.swift_api import SwiftAPI
from utils.core import SIMPLE_RESPONSE_REGEX, TEMP_RESPONSE_REGEX, send_cmd_sync_ok

# Software License Agreement (BSD License)
#
# Copyright (c) 2017, UFactory, Inc.
# All rights reserved.
#
# Author: Derwent <derwentx@gmail.com>

"""
This utility prints EEPROM values used to callibrate the uArm's reverse kinematics.
Is compatible with firmware version
"""

# logger_init(logging.VERBOSE)
logger_init(logging.DEBUG)
# logger_init(logging.INFO)

def main():
    logging.info('setup swift ...')
    swift = SwiftAPI()
    sleep(2)

    logging.info('device info: ')
    device_info = swift.get_device_info()
    logging.info(device_info)
    logging.info('firmware version:')
    fw_version = tuple(int(number) for number in device_info[2].split('.'))
    logging.info(fw_version)

    print('set mode to 3D print: %s' % send_cmd_sync_ok(swift, 'M2400 S2'))

    print('enable fan: %s' % send_cmd_sync_ok(swift, 'M106'))

    print('set temperature units: %s' % send_cmd_sync_ok(swift, 'M149 C'))

    # print('temperature hack: %s' % send_cmd_sync_ok(swift, 'M2213 V0'))

    print('set hotend to 205: %s' % send_cmd_sync_ok(swift, 'M104 S205'))

    print('wait for hotend...')
    while True:
        sleep(10)
        swift.flush_cmd()
        temp = send_cmd_sync_ok(swift, 'M105', TEMP_RESPONSE_REGEX)
        logging.info("temp is: %s" % temp)
        try:
            temp = float(temp)
        except ValueError:
            ValueError("Temp response was not a float: %s" % temp)

        if temp > 190:
            break

    print("retracting extruder...")
    response = send_cmd_sync_ok(swift, "G2204 E-60 F200")
    logging.debug("response: %s" % response)
    while True:
        response = send_cmd_sync_ok(swift, "G2204 E-10 F1000")
        logging.debug("response: %s" % response)

    print('done ...')
    while True:
        sleep(1)

if __name__ == '__main__':
    main()
