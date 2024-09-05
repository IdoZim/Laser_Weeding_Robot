### Laser Weeding Robot project Table of contacts
- [Overview](#overview)
    - [General explanation](#general-explanation)
    - [To do](#to-do)
- [Usage](#usage)
- [Main Script](#main-script)
- [Classes](#classes)
    - [first class](#first-class)
    - [second class](#second-class)
    ...
- [Support files](#support-files)
    - [](#)
    - [](#)
    ...

## Overview
### General explanation
- The main code is running through the `gui.py` file.
- From the gui, connect to the camera, connect to laser and to the robot. 
- The camera will detect green targets and mark them.
- **Home** button will bring the robot to it's home position.
- **Save** button will save the detected targets coordinates into `points` variable.
- `points` it is an array which each elements is an [x,y,z] array in the camera's coordinate system.
- After saving the coordinates from the camera the points array will be used to generate `targets` array.
- `targets` array contains the targets coordinates in the robot frame.
- **Move To** button will send the robot to the next target point. it will bring the center of the camera to the center of the target and will turn on the laser.
- **Correction** button will calculate the distance between the target and the laser and will send a correction movement to the robot.
- To set the required distance between the robot and the target - modify the `distance` variable in `create_targets` function

### To do
- Next step is to conduct series of experiments to measure the errors between the commands and the actual movements.
- another mission is to save the dx dy from the correction and add it to the next point movement (?)
- Each experiment is for a specific `distance`.

**Conduct for few different distances**

**In each step save the target position and the actual position into Pandas DaraFrame**

#### Experiments steps:
1. From *Home* position, detect the targets.
2. Go to the targets using `Move To`.
3. Correct the position using `Correction`.
4. Move to the next target.
5. Repeat the experiment with: *point -> Home -> point*

## Usage
1. Create connection to the camera and the laser using `Camera connect` button
2. Create connection to the robot using `Robot connect` button
3. Define the required distance from the target and submit it
4. Take the robot to it's Home position `Home` button
5. Create targets using `save` button
6. Move through the targets using `Move to` button
7. *optional*: Make correction with `Correction` button
8. Enter file name and create excle file
## Main script
**explain** with bold
- explain with bullets
- **bullet and bold**
## Classes
### first class
- explain sith bullets
- *somthing special* : `Variable_from_code`, can add somthing to copy
 ```python
 what what
 ```
### second class
## Support files