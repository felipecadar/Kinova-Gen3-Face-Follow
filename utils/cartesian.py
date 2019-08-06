#! /usr/bin/env python3

###
# KINOVA (R) KORTEX (TM)
#
# Copyright (c) 2018 Kinova inc. All rights reserved.
#
# This software may be modified and distributed
# under the terms of the BSD 3-Clause license.
#
# Refer to the LICENSE file for details.
#
###

import pygame

import time

from kortex_api.UDPTransport import UDPTransport
from kortex_api.RouterClient import RouterClient

from kortex_api.SessionManager import SessionManager

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.client_stubs.DeviceManagerClientRpc import DeviceManagerClient

from kortex_api.autogen.messages import Session_pb2, Base_pb2, Common_pb2

import curses

def twist_command(base_client_service, x, y, z, tx, ty, tz):
    command = Base_pb2.TwistCommand()
    command.mode = Base_pb2.UNSPECIFIED_TWIST_MODE
    command.duration = 2  # Unlimited time to execute

    twist = command.twist
    twist.linear_x = x
    twist.linear_y = y
    twist.linear_z = z
    twist.angular_x = tx
    twist.angular_y = ty
    twist.angular_z = tz
    base_client_service.SendTwistCommand(command)

def main(stdscr):
    # do not wait for input when calling getch
    stdscr.nodelay(1)

    a = 97
    z = 122
    s = 115
    x = 120
    d = 100
    c = 99
    f = 102
    v = 118
    g = 103
    b = 98
    h = 104
    n = 110


    movs = {
        a: ( 1,0,0,0,0,0) ,
        z: (-1,0,0,0,0,0),
        s: (0, 1,0,0,0,0),
        x: (0,-1,0,0,0,0),
        d: (0,0, 1,0,0,0),
        c: (0,0,-1,0,0,0),
        f: (0,0,0, 1,0,0),
        v: (0,0,0,-1,0,0),
        g: (0,0,0,0, 1,0),
        b: (0,0,0,0,-1,0),
        h: (0,0,0,0,0, 1),
        n: (0,0,0,0,0,-1)
    }

    while True:
        # get keyboard input, returns -1 if none available
        c = stdscr.getch()
        if c == 113:
            exit()
        elif c == 10:
                action_type = Base_pb2.RequestedActionType()
                action_type.action_type = Base_pb2.REACH_JOINT_ANGLES
                action_list = base_client_service.ReadAllActions(action_type)
                action_handle = None
                
                for action in action_list.action_list:
                    if action.name == "Home":
                        action_handle = action.handle

                base_client_service.ExecuteActionFromReference(action_handle)
                time.sleep(10)
        elif c != -1:

            if c in movs.keys():            
                x, y, z, tx, ty, tz = movs[c]
                pos = "Going to {} {} {} {} {} {}".format(x, y, z, tx, ty, tz)

                twist_command(base_client_service, x, y, z, tx, ty, tz)

                # print numeric value
                stdscr.addstr(pos + " ")
                stdscr.refresh()
                # return curser to start position
                stdscr.move(0, 0)
            else:
                twist_command(base_client_service, 0, 0, 0, 0, 0, 0)
                stdscr.addstr("Stoped ")
                stdscr.refresh()
                # return curser to start position
                stdscr.move(0, 0)

        else:
            twist_command(base_client_service, 0, 0, 0, 0, 0, 0)
            stdscr.addstr("Stoped ")
            stdscr.refresh()
            # return curser to start position
            stdscr.move(0, 0)

if __name__ == "__main__":

    DEVICE_IP = "192.168.1.10"
    DEVICE_PORT = 10000

    # Setup API
    errorCallback = lambda kException: print("_________ callback error _________ {}".format(kException))
    transport = UDPTransport()
    router = RouterClient(transport, errorCallback)
    transport.connect(DEVICE_IP, DEVICE_PORT)

    # Create session
    print("\nCreating session for communication")
    session_info = Session_pb2.CreateSessionInfo()
    session_info.username = 'admin'
    session_info.password = 'admin'
    session_info.session_inactivity_timeout = 60000   # (milliseconds)
    session_info.connection_inactivity_timeout = 2000 # (milliseconds)
    print("Session created")

    session_manager = SessionManager(router)   
    session_manager.CreateSession(session_info)

    # Create required services
    base_client_service = BaseClient(router)
    device_manager_service = DeviceManagerClient(router)

    # Find the number of actuator in angular action and trajectory
    sub_device_info = device_manager_service.ReadAllDevices()
    act_count = 0
    for dev in sub_device_info.device_handle:
        if dev.device_type is Common_pb2.BIG_ACTUATOR or dev.device_type is Common_pb2.SMALL_ACTUATOR:
            act_count += 1

    # Move arm to ready position
    print("\nMoving the arm to a safe position before executing example")
    action_type = Base_pb2.RequestedActionType()
    action_type.action_type = Base_pb2.REACH_JOINT_ANGLES
    action_list = base_client_service.ReadAllActions(action_type)
    action_handle = None
    # print("Actions:")
    # print( action_list.action_list)
    
    for action in action_list.action_list:
        if action.name == "Home":
            action_handle = action.handle

    if action_handle == None:
        import sys
        print("\nCan't reach safe position. Exiting")
        sys.exit(0)

    base_client_service.ExecuteActionFromReference(action_handle)
    time.sleep(5) # Leave time to action to complete
    # example_cartesian_action_movement(base_client_service)

    curses.wrapper(main)

    # # Example core
    # example_angular_action_movement(base_client_service)
    # example_cartesian_action_movement(base_client_service)
    # example_angular_trajectory_movement(base_client_service)
    # example_cartesian_trajectory_movement(base_client_service)

    # Close API session
    session_manager.CloseSession()

    # Deactivate the router and cleanly disconnect from the transport object
    router.SetActivationStatus(False)
    transport.disconnect()



