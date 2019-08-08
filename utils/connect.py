from kortex_api.UDPTransport import UDPTransport
from kortex_api.RouterClient import RouterClient, RouterClientSendOptions
from kortex_api.SessionManager import SessionManager

from kortex_api.autogen.client_stubs.VisionConfigClientRpc import VisionConfigClient
from kortex_api.autogen.client_stubs.DeviceConfigClientRpc import DeviceConfigClient
from kortex_api.autogen.client_stubs.DeviceManagerClientRpc import DeviceManagerClient

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient

from kortex_api.autogen.messages import Session_pb2, Base_pb2, Common_pb2
from kortex_api.autogen.messages import DeviceConfig_pb2, Session_pb2, DeviceManager_pb2, VisionConfig_pb2


def disconect():
    session_manager.CloseSession()
    router.SetActivationStatus(False)
    transport.disconnect()


DEVICE_IP = "192.168.1.10"
DEVICE_PORT = 10000

# Setup API
errorCallback = lambda kException: print("_________ callback error _________ {}".format(kException))
transport = UDPTransport()
router = RouterClient(transport, errorCallback)
transport.connect(DEVICE_IP, DEVICE_PORT)

# Create session
session_info = Session_pb2.CreateSessionInfo()
session_info.username = 'admin'
session_info.password = 'admin'
session_info.session_inactivity_timeout = 60000   # (milliseconds)
session_info.connection_inactivity_timeout = 2000 # (milliseconds)

session_manager = SessionManager(router)
session_manager.CreateSession(session_info)

# Create required services

# Create required services
device_manager_service = DeviceManagerClient(router)
vision_config_service = VisionConfigClient(router)
base_client_service = BaseClient(router)


