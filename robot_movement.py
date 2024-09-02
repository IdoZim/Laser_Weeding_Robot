import sys
import os
import time
import threading

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.client_stubs.BaseCyclicClientRpc import BaseCyclicClient
from kortex_api.RouterClient import RouterClientSendOptions
from kortex_api.autogen.messages import Session_pb2
from kortex_api.SessionManager import SessionManager
from kortex_api.autogen.messages import Base_pb2, BaseCyclic_pb2, Common_pb2

TIMEOUT_DURATION = 20

# Create closure to set an event after an END or an ABORT
def check_for_end_or_abort(e):
    """Return a closure checking for END or ABORT notifications

    Arguments:
    e -- event to signal when the action is completed
        (will be set when an END or ABORT occurs)
    """
    def check(notification, e = e):
        print("EVENT : " + \
              Base_pb2.ActionEvent.Name(notification.action_event))
        if notification.action_event == Base_pb2.ACTION_END \
        or notification.action_event == Base_pb2.ACTION_ABORT:
            e.set()
    return check

def move_to_home_position(base, base_cyclic):
    # Make sure the arm is in Single Level Servoing mode
    base_servo_mode = Base_pb2.ServoingModeInformation()
    base_servo_mode.servoing_mode = Base_pb2.SINGLE_LEVEL_SERVOING
    base.SetServoingMode(base_servo_mode)
    
    # Move arm to ready position
    print("Moving the arm to a safe position")
    action_type = Base_pb2.RequestedActionType()
    action_type.action_type = Base_pb2.REACH_JOINT_ANGLES
    action_list = base.ReadAllActions(action_type)
    action_handle = None
    for action in action_list.action_list:
        if action.name == "Home":
            action_handle = action.handle

    if action_handle == None:
        print("Can't reach safe position. Exiting")
        return False

    e = threading.Event()
    notification_handle = base.OnNotificationActionTopic(
        check_for_end_or_abort(e),
        Base_pb2.NotificationOptions()
    )

    base.ExecuteActionFromReference(action_handle)
    finished = e.wait(TIMEOUT_DURATION)
    base.Unsubscribe(notification_handle)

    if finished:
        print("Safe position reached")
    else:
        print("Timeout on action notification wait")
    
    return finished

def get_current_pose(base_cyclic):
    feedback = base_cyclic.RefreshFeedback()
    x = feedback.base.tool_pose_x 
    y = feedback.base.tool_pose_y
    z = feedback.base.tool_pose_z
    theta_x = feedback.base.tool_pose_theta_x  
    theta_y = feedback.base.tool_pose_theta_y 
    theta_z = feedback.base.tool_pose_theta_z
    current_pose = [x,y,z,theta_x,theta_y,theta_z]
    return current_pose

def cartesian_action_movement(base, base_cyclic, target): # Set 6 coordinates to end effctor (x,y,z, angles)
    
    print("Starting Cartesian action movement ...")
    action = Base_pb2.Action()
    action.name = "Example Cartesian action movement"
    action.application_data = ""

    feedback = base_cyclic.RefreshFeedback()

    cartesian_pose = action.reach_pose.target_pose
    cartesian_pose.x = target[0]            # (meters)
    cartesian_pose.y = target[1]            # (meters)
    cartesian_pose.z = target[2]            # (meters) ((for relative movement: feedback.base.tool_pose_z  + relative move))
    cartesian_pose.theta_x = feedback.base.tool_pose_theta_x  # + angular_move[0] # (degrees)
    cartesian_pose.theta_y = feedback.base.tool_pose_theta_y #angular_move[1] # (degrees)
    cartesian_pose.theta_z = feedback.base.tool_pose_theta_z #+ angular_move[2] # (degrees)

    e = threading.Event()
    notification_handle = base.OnNotificationActionTopic(
        check_for_end_or_abort(e),
        Base_pb2.NotificationOptions()
    )

    print("Executing action")
    base.ExecuteAction(action)

    print("Waiting for movement to finish ...")
    finished = e.wait(TIMEOUT_DURATION)
    base.Unsubscribe(notification_handle)

    if finished:
        print("Cartesian movement completed")
    else:
        print("Timeout on action notification wait")
    return finished