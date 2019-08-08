import numpy as np

import cv2
import dlib
import time

from videocaptureasync import VideoCaptureAsync

from kortex_api.UDPTransport import UDPTransport
from kortex_api.RouterClient import RouterClient

from kortex_api.SessionManager import SessionManager

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient

from kortex_api.autogen.messages import Session_pb2, Base_pb2


def send_home(base_client_service):
    print('Going Home....')
    action_type = Base_pb2.RequestedActionType()
    action_type.action_type = Base_pb2.REACH_JOINT_ANGLES
    action_list = base_client_service.ReadAllActions(action_type)
    action_handle = None
    
    for action in action_list.action_list:
        if action.name == "Home":
            action_handle = action.handle

    base_client_service.ExecuteActionFromReference(action_handle)
    time.sleep(6)
    print(" Done!")

def get_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return (x2-x1, y2-y1)

def twist_command(base_client_service, cmd):
    command = Base_pb2.TwistCommand()
    command.mode = Base_pb2.UNSPECIFIED_TWIST_MODE
    command.duration = 2  # Unlimited time to execute

    x, y, z, tx, ty, tz = cmd

    twist = command.twist
    twist.linear_x = x
    twist.linear_y = y
    twist.linear_z = z
    twist.angular_x = tx
    twist.angular_y = ty
    twist.angular_z = tz
    base_client_service.SendTwistCommand(command)

if __name__ == "__main__":

    DEVICE_IP = "192.168.1.10"
    DEVICE_PORT = 10000

    # Setup API
    errorCallback = lambda kException: print("_________ callback error _________ {}".format(kException))
    transport = UDPTransport()
    router = RouterClient(transport, errorCallback)
    transport.connect(DEVICE_IP, DEVICE_PORT)

    # Create session
    print("Creating session for communication")
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

    send_home(base_client_service)

    video_capture = VideoCaptureAsync("rtsp://192.168.1.10/color")
    detector = dlib.get_frontal_face_detector()

    FACTOR = 0.3
    VEL = 1
    movs = {
        "look_up": np.array((0,0,0,-VEL,0,0)),
        "look_left": np.array((0,0,0,0, VEL,0)),
        "stop": np.array((0,0,0,0,0,0))
    }

    video_capture.start()
    while True:
        ret, frame = video_capture.read()

        center_X = int(frame.shape[1]/2)
        center_Y = int(frame.shape[0]/2)
        
        start = time.time()

        res = cv2.resize(frame, None, fx=FACTOR, fy=FACTOR)
        gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        rects = detector(gray)    
        
        cmd = np.zeros(6)

        for (i, rect) in enumerate(rects):
            x1 = int(rect.left() / FACTOR)
            y1 = int(rect.top() / FACTOR)
            x2 = int(rect.right() / FACTOR)
            y2 = int(rect.bottom() / FACTOR)
            face_center = (int((x1+x2)/2), int((y1+y2)/2))

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (center_X, center_Y), 2, (255, 0, 0), 2)

            distance = get_distance(face_center, (center_X, center_Y))
            if distance[0] > 100 or distance[0] < -100:
                cmd += movs["look_left"] * distance[0] * 0.005

            if distance[1] > 100 or distance[1] < -100:
                cmd += movs["look_up"] * distance[1] * 0.005

            cmd = np.clip(cmd, -2, 2)

            continue

        twist_command(base_client_service, list(cmd))

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        end = time.time()

        print(chr(27) + "[2J")  # Clear terminal
        print("Center = {}\nVel Vec = {}\nFPS: {}\nFaces: {}".format((center_X, center_Y), cmd, 1/(end - start), len(rects)))

    video_capture.stop()
    cv2.destroyAllWindows()

    send_home(base_client_service)

    print('Closing Session..')
    session_manager.CloseSession()
    router.SetActivationStatus(False)
    transport.disconnect()
    print('Done!')