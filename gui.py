from tkinter import *
import sys
import os
import time
import threading
import robot_movement
import utilities
from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.client_stubs.BaseCyclicClientRpc import BaseCyclicClient
from kortex_api.RouterClient import RouterClientSendOptions
from kortex_api.SessionManager import SessionManager
from kortex_api.autogen.messages import Session_pb2
from kortex_api.autogen.messages import Base_pb2, BaseCyclic_pb2, Common_pb2
import shape_detector
import laser_switch
import serial

TIMEOUT_DURATION = 20

## Robot base
base = None
base_cyclic = None
device_connection = None

# Target points handle
camera_xyz = [0,0,0]
points=[]
point = 0
current_pose = []
targets = []

arduino = None
laser_on = '0'

def close_window():
    global base, base_cyclic, device_connection, arduino
    if device_connection:
        if device_connection.sessionManager:
            router_options = RouterClientSendOptions()
            router_options.timeout_ms = 1000
            device_connection.sessionManager.CloseSession(router_options)
            device_connection.transport.disconnect()
    base = None
    base_cyclic = None
    device_connection = None
    laser_switch.disconnect(arduino, '1')
    window.destroy()

def connect_to_robot():
    global base, base_cyclic, device_connection, current_pose
    # Import the utilities helper module
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import utilities
    # Parse arguments
    args = utilities.parseConnectionArguments()
    # Create connection to the device and get the router
    device_connection = utilities.DeviceConnection(args.ip, port=utilities.DeviceConnection.TCP_PORT, credentials=(args.username, args.password))
    device_connection.transport.connect(device_connection.ipAddress, device_connection.port)

    if device_connection.credentials[0] != "":
        session_info = Session_pb2.CreateSessionInfo()
        session_info.username = device_connection.credentials[0]
        session_info.password = device_connection.credentials[1]
        session_info.session_inactivity_timeout = 10000  # (milliseconds)
        session_info.connection_inactivity_timeout = 2000  # (milliseconds)

        device_connection.sessionManager = SessionManager(device_connection.router)
        print("Logging as", device_connection.credentials[0], "on device", device_connection.ipAddress)
        device_connection.sessionManager.CreateSession(session_info)

    # Create required services
    base = BaseClient(device_connection.router)
    base_cyclic = BaseCyclicClient(device_connection.router)
    current_pose = robot_movement.get_current_pose(base_cyclic)
    print("Robot Connected")

def move_to_home_pos():
    global base, base_cyclic, device_connection, current_pose
    laser_point('0')
    robot_movement.move_to_home_position(base, base_cyclic)
    current_pose = robot_movement.get_current_pose(base_cyclic)
    print("Home")
    
def move_to():
    global base, base_cyclic, device_connection, camera_xyz, point,points
    target = targets[point]
    laser_point('0')
    print(f"Moving to point {point}")
    finish = robot_movement.cartesian_action_movement(base, base_cyclic, target)
    if finish:
        laser_point('1')
    point = point + 1
    if len(points) > point:
        camera_xyz = points[point]
        
    else:
        point = 0
        camera_xyz = points[point]
        print("Finished all points")

def create_targets():
    global targets, camera_xyz, current_pose, points
    targets = []    
    for j in range(len(points)):
        target = [0, 0, 0, 0, 0, 0] # X, Y, Z, t_x, t_y, t_z
        camera_xyz = points[j]

        if camera_xyz[2] > 0.3:
            target[0] = current_pose[0] + camera_xyz[2] - 0.3  # Robot's X = Camera's Z
        else:
            target[0] = current_pose[0]
        target[1] = current_pose[1] + (-camera_xyz[0])  # Robot's Y = Camera's X
        target[2] = current_pose[2] + (-camera_xyz[1])    # Robot's Z = Camera's Y
        targets.append(target)

def camera_save():
    global points, current_pose, base_cyclic, point
    point = 0
    points = []
    points =shape_detector.save_current_frame(0) # Camera's X,Y,Z TODO: convert to robot's XYZ
    center_xyz_label.config(text=f' Number of points : {len(points)}')
    current_pose = robot_movement.get_current_pose(base_cyclic)
    print(points)
    create_targets()

def camera_connect():
    shape_detector.start_camera()
    print("Camera Connected")

def laser_connect():
    global arduino
    arduino = laser_switch.connect()
    print("Laser Connected")

def laser_point(laser_on):
    global arduino 
    laser_switch.send_command(arduino, laser_on)
    

## GUI settingss ##

window = Tk()
window.title("Laser Weeding Robot")
window.minsize(width=700, height=500)
window.config(padx=10, pady=20, bg="#071952")

robot_label = Label(padx=100, text="Robot", font=("Arial", 36), bg="#071952", fg="white")
robot_label.grid(column=0, row=0)

camera_label = Label(padx=100, text="Camera", font=("Arial", 36), bg="#071952", fg="white")
camera_label.grid(column=2, row=0)

connect_button = Button(text="Connect", command=connect_to_robot)
connect_button.place(x=110, y=70)

home_button = Button(text="Home", command=move_to_home_pos)
home_button.place(x=190, y=70)

move_button = Button(text="Move to", command=move_to)
move_button.place(x=190, y=110)

camera_connect_button = Button(text="Connect", command=camera_connect)
camera_connect_button.place(x=440, y=70)

camera_save_button = Button(text="Save", command=camera_save)
camera_save_button.place(x=520, y=70)

laser_button = Button(text="Laser", command=laser_point)
laser_button.place(x=400, y=130)

laser_connection = Button(text="Laser connect", command=laser_connect)
laser_connection.place(x=440, y=130)

center_xyz_label = Label(text="X, Y, Z")
center_xyz_label.place(x=520, y=100)

# angles_label = Label(text="X, Y, Z")
# angles_label.place(x=520, y=140)

# window.protocol("WM_DELETE_WINDOW", close_window)
window.mainloop()
