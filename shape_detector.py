import pyrealsense2 as rs
import numpy as np
import cv2
import threading
import time
import math

# Global variables for the RealSense camera
pipeline = None
align = None
depth_frame = None
color_frame = None
current_frame = None
colorizer = None

relative_xyz = [0, 0, 0]
points=[]

frame_center = (640, 360)  # Center of the 1280X720 frame

def start_camera():
    global pipeline, align
    # Initialize camera
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 6)
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 6)
    profile = pipeline.start(config)

    colorizer = rs.colorizer()
    align = rs.align(rs.stream.depth)

    # align_to = rs.stream.color
    # align = rs.align(align_to)

    # Start the camera thread
    threading.Thread(target=update_frame, daemon=True).start()

def update_frame(flag=1):
    global current_frame, relative_xyz, points
    trig = 1
    while trig:
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        aligned_color_frame = aligned_frames.get_color_frame()
        color_image = np.asanyarray(aligned_color_frame.get_data())
        depth = frames.get_depth_frame()

        # Convert BGR to HSV for color detection
        hsv_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
        # green_range = ((35, 50, 40), (105, 150, 255))
        green_range = ((35, 50, 40), (55, 200, 255))
        mask = cv2.inRange(hsv_image, green_range[0], green_range[1])

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ind = -1
        for contour in contours:
            ind += 1
            contArea = cv2.contourArea(contour)
            if contArea > 5:
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.intp(box)
                # cv2.drawContours(color_image,[box],0,(0,0,255),2)
                M = cv2.moments(contour)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                # cx, cy = rect[0]
                cx, cy = int(cx), int(cy)
                z_depth = depth.get_distance(int(cx), int(cy))
                # Deproject the pixel to a 3D point
                intrinsics = depth.profile.as_video_stream_profile().intrinsics
                point_in_3d = rs.rs2_deproject_pixel_to_point(intrinsics, [cx, cy], z_depth)
                if 0.25 < point_in_3d[2] < 1.1:
                    cv2.drawContours(color_image,contours,ind,(255,0,255),-1)
                    cv2.circle(color_image, (cx,cy),3, (0,255,0),thickness=1)
                    print_str = [float(point_in_3d[0]), float(point_in_3d[1]), float(point_in_3d[2])]
                    print_str = str([round(num,3) for num in print_str])
                    cv2.putText(color_image, print_str, (cx-200, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                    hsv = [hsv_image[cy,cx,:]]
                    cv2.putText(color_image, str(hsv), (cx, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                    if flag == 0:
                        xyz = [float(point_in_3d[0]), float(point_in_3d[1]), float(point_in_3d[2])]
                        # xyz = [round(num,3) for num in xyz]
                        points.append(xyz)
        cv2.circle(color_image, frame_center,3, (0,255,255),thickness=1)
        # relative_xyz = [float(point_in_3d[0]), float(point_in_3d[1]), float(point_in_3d[2])]
        current_frame = color_image
        trig = flag

def save_current_frame(f):
    global current_frame, points
    points = []
    update_frame(f)
    if current_frame is not None:
        return points
    

def show_camera_feed():
    while True:
        if current_frame is not None:
            cv2.imshow('RealSense', current_frame)
        if cv2.waitKey(1) == ord('q'):
            break
    cv2.destroyAllWindows()

# Start showing the camera feed in a separate thread
threading.Thread(target=show_camera_feed, daemon=True).start()
