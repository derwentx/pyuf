#!/usr/bin/env python3
from __future__ import print_function

import os
import sys
from collections import OrderedDict
from time import sleep

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.core import send_cmd_sync_ok, SIMPLE_RESPONSE_REGEX
from uf.utils.log import logger_init, logging
from uf.wrapper.swift_api import SwiftAPI

# Software License Agreement (BSD License)
#
# Copyright (c) 2017, UFactory, Inc.
# All rights reserved.
#
# Author: Duke Fong <duke@ufactory.cc> / Derwent <derwentx@gmail.com>

"""
This utility prints EEPROM values used to callibrate the uArm's reverse kinematics.
Is compatible with firmware version
"""

# logger_init(logging.VERBOSE)
# logger_init(logging.DEBUG)
logger_init(logging.INFO)

def main():
    print('setup swift ...')
    swift = SwiftAPI()
    sleep(2)

    print('device info: ')
    device_info = swift.get_device_info()
    print(device_info)
    print('firmware version:')
    fw_version = tuple(int(number) for number in device_info[2].split('.'))
    print(fw_version)
    fw_has_b_angles = (fw_version >= (3, 1, 16))

    print('EEPROM Values: ')
    print('-> reference_angle_value:')
    # in uArmParams.h
    # define EEPROM_ON_CHIP                         0
    # define EEPROM_REFERENCE_VALUE_ADDR            800
    # define EEPROM_REFERENCE_VALUE_B_FLAG_ADDR     818
    # define EEPROM_REFERENCE_VALUE_B_ADDR          820
    # define DATA_TYPE_BYTE                         1
    # define DATA_TYPE_INTEGER                      2
    #
    # in uArmCalibration.cpp
    # uint8_t reference_angle_flag =
    #     getE2PROMData(EEPROM_ON_CHIP, EEPROM_REFERENCE_VALUE_B_FLAG_ADDR, DATA_TYPE_BYTE);
    # reference_angle_value[X_AXIS] =
    #     getE2PROMData(EEPROM_ON_CHIP, EEPROM_REFERENCE_VALUE_ADDR, DATA_TYPE_INTEGER);
	# reference_angle_value[Y_AXIS] =
    #     getE2PROMData(EEPROM_ON_CHIP, EEPROM_REFERENCE_VALUE_ADDR+2, DATA_TYPE_INTEGER);
    # reference_angle_value[Z_AXIS] =
    #     getE2PROMData(EEPROM_ON_CHIP, EEPROM_REFERENCE_VALUE_ADDR+4, DATA_TYPE_INTEGER);
    reference_angle_flag = 0
    if fw_has_b_angles:
        reference_angle_flag = send_cmd_sync_ok(swift, 'M2211 N0 A818 T1')
    reference_angle_value = []
    reference_angle_addr = 800
    if reference_angle_flag:
        reference_angle_addr = 820
    for offset in range(0, 6, 2):
        reference_angle_value.append(send_cmd_sync_ok(
            swift,
            'M2211 N0 A%d T2' % (reference_angle_addr + offset),
            SIMPLE_RESPONSE_REGEX
        ))
    print(reference_angle_value)

    print("-> height offset:")
    # in uArmParams.h
    # define EEPROM_HEIGHT_ADDR	    910
    # define DATA_TYPE_FLOAT        4

    # in uArmCalibration.cpp
    # getE2PROMData(EEPROM_ON_CHIP, EEPROM_HEIGHT_ADDR, DATA_TYPE_FLOAT);
    height_offset = send_cmd_sync_ok(swift, "M2211 N0 A910 T4", SIMPLE_RESPONSE_REGEX)
    print(height_offset)

    print("-> front offset:")
    # in uArmParams.h
    # define EEPROM_FRONT_ADDR      920

    # in uArmCalibration.cpp
    # getE2PROMData(EEPROM_ON_CHIP, EEPROM_FRONT_ADDR, DATA_TYPE_FLOAT);
    front_offset = send_cmd_sync_ok(swift, "M2211 N0 A920 T4", SIMPLE_RESPONSE_REGEX)
    print(front_offset)

    # print('resetting...')
    # swift.reset()

    # swift.set_servo_detach(2, wait=True)
    # sleep(1)
    # swift.set_servo_detach(1, wait=True)
    # sleep(1)
    # swift.set_servo_detach(0, wait=True)
    swift.set_servo_detach(wait=True)
    print("Servos detatched")

    # print("now you can position the arm on the X-Z plane (rotation locked at zero)")

    while True:
        sleep(1)
        print("Make your selection:")
        print(" - Press enter to get calibration data")
        print(" - Press s to set reference angle")
        if fw_has_b_angles:
            print(" - Press b to set reference angle B")
        else:
            print(" - [reference angle B not supported by firmware %s]" % fw_version)
        print(" - Press h to zero height")
        print(" - Press Ctrl-C to exit")
        raw_in = input("...")
        # swift.set_servo_attach(wait=True)
        # print("get_position: %s" % swift.get_position())

        # hack to update current position on device
        send_cmd_sync_ok(swift, "M2400 S1")

        values = OrderedDict()

        # Raw sensor values
        response = send_cmd_sync_ok(swift, "P2242")
        values['sensor'] = OrderedDict([
            (token[0], token[1:]) for token in response.split(" ")[1:]
        ])

        # Cartesian coordinates
        response = send_cmd_sync_ok(swift, "P2220")
        values['cartesian'] = OrderedDict([
            (token[0], token[1:]) for token in response.split(" ")[1:]
        ])

        # angle values
        values['angle'] = OrderedDict()
        for index, name in [
                (0, 'B'),
                (1, 'L'),
                (2, 'R')
        ]:
            response = send_cmd_sync_ok(swift, "P2206 N%s" % index)
            values['angle'][name] = response.split(" ")[1][1:]

        print("; ".join([
            ", ".join([
                "%s:%+07.2f" % (key, float(value)) for key, value in values[dictionary].items()
            ]) for dictionary in ['sensor', 'cartesian', 'angle']
        ]))

        if raw_in == "s":
            print("M2401: %s" % send_cmd_sync_ok(swift, "M2401 V22765"))
        elif fw_has_b_angles and raw_in == "b":
            print("M2401: %s" % send_cmd_sync_ok(swift, "M2401 B"))
        elif raw_in == "h":
            print("M2410: %s" % send_cmd_sync_ok(swift, "M2410"))
        else:
            logging.warning("did not understand command: %s" % raw_in)


        # swift.set_buzzer()
        # swift.set_servo_detach(wait=True)

    print('done ...')
    while True:
        sleep(1)

if __name__ == '__main__':
    main()
