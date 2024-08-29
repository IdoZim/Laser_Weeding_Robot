import pyrealsense2 as rs
import numpy as np
import cv2
import math

def get_profiles():
    ctx = rs.context()
    devices = ctx.query_devices()
    color_profiles = []
    depth_profiles = []

    for device in devices:
        name = device.get_info(rs.camera_info.name)
        serial = device.get_info(rs.camera_info.serial_number)
        print('Sensor: {}, {}'.format(name, serial))
        print('Supported video formats:')
        for sensor in device.query_sensors():
            for stream_profile in sensor.get_stream_profiles():
                stream_type = str(stream_profile.stream_type())

                if stream_type in ['stream.color', 'stream.depth']:
                    v_profile = stream_profile.as_video_stream_profile()
                    fmt = stream_profile.format()
                    w, h = v_profile.width(), v_profile.height()
                    fps = v_profile.fps()

                    video_type = stream_type.split('.')[-1]
                    print('  {}: width={}, height={}, fps={}, fmt={}'.format(
                        video_type, w, h, fps, fmt))
                    if video_type == 'color':
                        color_profiles.append((w, h, fps, fmt))
                    else:
                        depth_profiles.append((w, h, fps, fmt))

    return color_profiles, depth_profiles

# print(get_profiles())

# Initialize Intel RealSense camera
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 6)
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 6)
profile = pipeline.start(config)

colorizer = rs.colorizer()
align = rs.align(rs.stream.depth)

# Create mask for green color
green_range = ((35, 50, 40), (105, 150, 255))


# Create mask for red color
red_range1 = ((0, 50, 40), (30, 200, 255))
red_range2 = ((160, 50, 40), (250, 200, 255))

# Frame dimensions
frame_width = 1280
frame_height = 720
frame_center = (frame_width // 2, frame_height // 2)

points = []

try:
    while True:
        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        aligned_color_frame = aligned_frames.get_color_frame()
        color_image = np.asanyarray(aligned_color_frame.get_data())
        depth = frames.get_depth_frame()
        intrinsics = depth.profile.as_video_stream_profile().intrinsics
        # Convert BGR to HSV for color detection
        hsv_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)


        mask = cv2.inRange(hsv_image, green_range[0], green_range[1])
        mask2= cv2.inRange(hsv_image, red_range1[0], red_range1[1])
        mask3= cv2.inRange(hsv_image, red_range2[0], red_range2[1])
        mask_red = mask2+mask3


        # Find contours
        contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # color_image = cv2.drawContours(color_image, contours, -1, (255,0,0),2)
        ind = -1
        for contour in contours:
            ind += 1
            contArea = cv2.contourArea(contour)
            if contArea > 1:
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.intp(box)
                M = cv2.moments(contour)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                # cx, cy = rect[0]
                cx, cy = int(cx), int(cy)
                z_depth = depth.get_distance(int(cx), int(cy))
                # Deproject the pixel to a 3D point
                point_in_3d = rs.rs2_deproject_pixel_to_point(intrinsics, [cx, cy], z_depth)
                if 0.3 < point_in_3d[2] < 1.0:
                    cv2.drawContours(color_image,contours,ind,(255,0,255),-1)
                    cv2.circle(color_image, (cx,cy),5, (0,255,0),thickness=1)
                    print_str = point_in_3d.__str__()
                    xyz = [float(point_in_3d[0]), float(point_in_3d[1]), float(point_in_3d[2])]
                    xyz = [round(num, 2) for num in xyz]
                    hsv = [hsv_image[cy,cx,:]]
                    cv2.putText(color_image, str(xyz), (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                    cv2.putText(color_image, str(hsv), (cx, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                
                    points.append(xyz)
            
                

        cv2.circle(color_image, frame_center,5, (0,255,255),thickness=1)
        # Display the image with detections
        # cv2.imshow('RealSense', mask)
        
        # # Break the loop if 'q' is pressed
        # if cv2.waitKey(1) == ord('q'):
        #     break
        cv2.imshow('RealSense', color_image)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) == ord('q'):
            break

finally:
    # Stop streaming
    pipeline.stop()
    cv2.destroyAllWindows()
