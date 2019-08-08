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


import time

from kortex_api.UDPTransport import UDPTransport
from kortex_api.RouterClient import RouterClient

from kortex_api.SessionManager import SessionManager

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.client_stubs.DeviceManagerClientRpc import DeviceManagerClient

from kortex_api.autogen.messages import Session_pb2, Base_pb2, Common_pb2

import curses
import pdb

def read_joints(base_client_service):
    state = base_client_service.GetMeasuredJointAngles().ListFields()[0][1] 
    angles = {}
    for j in state:
        angles[j.joint_identifier] = j.value
    return angles

def joint_angle_command(base_client_service, j_id, value):

    constrained_joint_angles = Base_pb2.ConstrainedJointAngles()
    state = read_joints(base_client_service)
    act_count = base_client_service.GetActuatorCount()

    for joint_id in range(act_count.count):
        joint_angle = constrained_joint_angles.joint_angles.joint_angles.add()
        joint_angle.joint_identifier = joint_id
        if joint_id == j_id:
            joint_angle.value = value
        else:
            joint_angle.value = state[joint_id]

        print("joint ID {}   Value {}".format(joint_angle.joint_identifier, joint_angle.value))


    base_client_service.PlayJointTrajectory(constrained_joint_angles)
    # time.sleep(10)

def joint_speed_command(base_client_service, j_id, value):

    speeds = Base_pb2.JointSpeeds()
    act_count = base_client_service.GetActuatorCount()
    js = speeds.joint_speeds.add()
    js.joint_identifier = j_id
    js.value = value

    # action = Base_pb2.Action()
    # action.name = "Example speed action"
    # action.application_data = ""

    # act_count = base_client_service.GetActuatorCount()

    # for joint_id in range(act_count.count):
    #     joint_speed = action.send_joint_speeds.joint_speeds.add()
    #     joint_speed.joint_identifier = joint_id
    #     if joint_id == j_id:
    #         joint_speed.value = value
    #     else:
    #         joint_speed.value = 0.1

    #     print("joint ID {} Speed Value {}".format(joint_speed.joint_identifier, joint_speed.value))


    # # base_client_service.PlayJointTrajectory(joint_speeds)
    # base_client_service.ExecuteAction(action)
    # time.sleep(10)

def joint_speed(base_client_service, joint_id, value):
    joint_speed = Base_pb2.JointSpeed()
    joint_speed.joint_identifier = joint_id  # Need to exclude base id
    joint_speed.value = value   # Speed in degrees/second
    joint_speed.duration = 0  # Unlimited time to execute
    base_client_service.SendSelectedJointSpeedCommand(joint_speed)

def main(stdscr):
    # do not wait for input when calling getch
    stdscr.nodelay(1)
    joint_value = 0

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
            if c == 44:
                joint_value += 5
            elif c == 46:
                joint_value -= 5

            joint_angle_command(base_client_service, 5, joint_value)
        # else:

            # joint_angle_command(base_client_service, 6, joint_value)

        stdscr.addstr(str(joint_value) + " ")
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

    # curses.wrapper(main)

    speed = int(input())
    while speed < 50:
        joint_speed_command(base_client_service, 6, speed)
        speed = int(input())

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



