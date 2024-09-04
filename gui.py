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
import pandas as pd

TIMEOUT_DURATION = 20
## Robot base
base = None
base_cyclic = None
device_connection = None

# Target points handle
points=[]
point = 0
current_pose = []
targets = []
distance = 0.3

arduino = None

headers = ["Point #", "Target x", "Target y", "Target z", "x", "y", "z", "Corrected x", "Corrected y", "Corrected z"]
df = pd.DataFrame(columns=headers)

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
    global base, base_cyclic, device_connection, current_pose, df
    laser_point('0')
    robot_movement.move_to_home_position(base, base_cyclic)
    current_pose = robot_movement.get_current_pose(base_cyclic)
    new_line = ["Home","Home_x", "Home_y", "Home_z" ,current_pose[0], current_pose[1], current_pose[2],None, None, None]
    df.loc[len(df)] = new_line
    print("Home")
    
def move_to():
    global point, df
    target = targets[point]
    laser_point('0')
    print(f"Moving to point {point}")
    finish = robot_movement.cartesian_action_movement(base, base_cyclic, target)
    if finish:
        laser_point('1')
        current_pose = robot_movement.get_current_pose(base_cyclic)
        new_line = [int(point + 1), target[0], target[1], target[2], current_pose[0], current_pose[1], current_pose[2], None, None, None]
        df.loc[len(df)] = new_line
    point = point + 1
    if len(points) <= point:
        point = 0
        print("Finished all points")
        

def create_targets():
    global targets, current_pose, points, file_name
    targets = []    
    current_pose = robot_movement.get_current_pose(base_cyclic)
    for j in range(len(points)):
        target = [0, 0, 0, 0, 0, 0] # X, Y, Z, t_x, t_y, t_z
        camera_xyz = points[j]

        if camera_xyz[2] > distance:
            target[0] = current_pose[0] + camera_xyz[2] - distance  # Robot's X = Camera's Z
        else:
            target[0] = current_pose[0]
        target[1] = current_pose[1] + (-camera_xyz[0])  # Robot's Y = Camera's X
        target[2] = current_pose[2] + (-camera_xyz[1])    # Robot's Z = Camera's Y
        targets.append(target)

def camera_save():
    global points, current_pose, point
    point = 0
    points = []
    points =shape_detector.save_current_frame(0) # Camera's X,Y,Z TODO: convert to robot's XYZ
    center_xyz_label.config(text=f' Number of points : {len(points)}')
    current_pose = robot_movement.get_current_pose(base_cyclic)
    create_targets()

def camera_connect():
    shape_detector.start_camera()
    print("Camera Connected")
    laser_connect()

def laser_point(laser_on):
    global arduino 
    laser_switch.send_command(arduino, laser_on)

def laser_connect():
    global arduino
    arduino = laser_switch.connect()
    print("Laser Connected")
    laser_point('0')

def correction():
    correct_offset = [0,0,0]
    current_pose = robot_movement.get_current_pose(base_cyclic)
    offset = shape_detector.correction()
    offset = [round(num,4) for num in offset]
    print(f"Offset= {offset}")
    correct_offset[0] = current_pose[0]
    correct_offset[1] = current_pose[1] + (-offset[0])  # Robot's Y = Camera's -X
    correct_offset[2] = current_pose[2] + (-offset[1])    # Robot's Z = Camera's -Y
    print(f"Current pos = {current_pose[:3]}")
    
    print(f"Command: {correct_offset}")
    robot_movement.cartesian_action_movement(base, base_cyclic, correct_offset)
    correct_offset = [0,0,0]
    current_pose = robot_movement.get_current_pose(base_cyclic)
        
def get_distance():
    global distance
    distance = (float(insert_distance.get())) / 100.0
    print(distance)

def clear_entry(event, default_text):
    if event.widget.get() == default_text:
        event.widget.delete(0, END)

def create_file():
    global df, distance
    file_name = str(insert_file_name.get()) + f"_distance_{distance*100}_cm.xlsx"
    df.to_excel(file_name, index=True, index_label='Step') 

## GUI settingss ##

window = Tk()
window.title("Laser Weeding Robot")
window.minsize(width=700, height=500)
window.config(padx=10, pady=20, bg="#071952")
###############################################
robot_label = Label(text="Robot", font=("Arial", 36), bg="#071952", fg="white")
robot_label.grid(column=0, row=0, columnspan=2, padx=100)

connect_button = Button(padx=15,text="Robot Connect", command=connect_to_robot)
connect_button.grid(column=0, row=1, pady=10)

home_button = Button(padx=15,text="Home", command=move_to_home_pos)
home_button.grid(column=1, row=1, pady=10)

move_button = Button(padx=15,text="Move to", command=move_to)
move_button.grid(column=0, row=2, pady=10)

correction_button = Button(padx=15,text="Correction", command=correction)
correction_button.grid(column=1, row=2, pady=10)
#########################################################
camera_label = Label(text="Camera", font=("Arial", 36), bg="#071952", fg="white")
camera_label.grid(column=2, row=0, columnspan=2, padx=100)

camera_connect_button = Button(padx=15,text="Camera Connect", command=camera_connect) # connect to camera and laser
camera_connect_button.grid(column=2, row=1, pady=10)

camera_save_button = Button(padx=15,text="Save", command=camera_save)
camera_save_button.grid(column=3, row=1, pady=10)

center_xyz_label = Label(text="Number of points")
center_xyz_label.grid(column=3, row=2, pady=10)
######################################################
settings_label = Label(padx=100, text="Settings", font=("Arial", 36), bg="#071952", fg="white")
settings_label.grid(column=0, row=3, columnspan=2, padx=100)

submit_settings = Button(padx=15, text='Submit distance', command=get_distance)
submit_settings.grid(column=1, row=4, pady=10)

insert_distance = Entry()
insert_distance.insert(0, 'Enter distance in cm')
insert_distance.bind("<FocusIn>", lambda event: clear_entry(event, "Enter distance in cm"))
insert_distance.grid(column=0, row=4, pady=10)

insert_file_name = Entry()
insert_file_name.insert(0, 'Enter file name')
insert_file_name.bind("<FocusIn>", lambda event: clear_entry(event, "Enter file name"))
insert_file_name.grid(column=0, row=5, pady=10)

submit_file = Button(padx=15, text='Create xlsx file', command=create_file)
submit_file.grid(column=1, row=5, pady=10)

# window.protocol("WM_DELETE_WINDOW", close_window)
window.mainloop()