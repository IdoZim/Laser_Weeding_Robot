import cv2
import numpy as np

# Load the image
image = cv2.imread('green_rectangle.jpg')

# Convert the image to HSV color space
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Define the green color range for the mask
lower_green = np.array([35, 100, 100])
upper_green = np.array([85, 255, 255])
mask = cv2.inRange(hsv, lower_green, upper_green)

# Find contours
contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Draw contours on the original image
for contour in contours:
    cv2.drawContours(image, [contour], -1, (0, 255, 0), 2)

# Display the result
cv2.imshow('Image with Green Contours', image)
cv2.imshow('Green Mask', mask)
cv2.waitKey(0)
cv2.destroyAllWindows()
