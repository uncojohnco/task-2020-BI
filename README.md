## Summary

Maya UI Tool to reset the scenes camera(s) clip plane values.
> TODO: Add video demo

## Install and displaying the UI

1. Download this repo
2. copy `reset_camera_clip_planes.py` into:
   - **Windows**: `$HOME/maya/scripts`
     e.g. on my instance of Windows it would be`C:/Users/johnco/Documents/maya/scripts`
3. From a `Python shell` in the `Maya Script Editor`, execute the below:
   - **Windows**:
   ```python
   import os

   script_path = "{home}/maya/scripts/reset_camera_clip_planes.py".format(home=os.path.expandvars("$HOME"))
   # e.g. "C:/Users/johnco/Documents/maya/scripts/reset_camera_clip_planes.py"
   execfile(script_path)
   ```
<img src="https://user-images.githubusercontent.com/7044060/94467554-21917a80-0191-11eb-91fb-a411ea3af11c.png" width="300" />

## Usage

With the tool open:<br>
<img src="https://user-images.githubusercontent.com/7044060/94468728-e728dd00-0192-11eb-90ff-a15252458ff7.png" width="400" />

### Reset Camera Clip Planes Operation

<img src="https://user-images.githubusercontent.com/7044060/94469218-b72e0980-0193-11eb-82f9-9600331f14cb.png" width="400" />
1. Set the clip plane values to desired values
> TODO: Add screen shot or gif
2. Choose the camera context to for the "Apply" operation to execute on.
   - Can either be run on the selected cameras in the scene
   - Or on all cameras

> TODO: Add screen shot or gif

> TODO: Add option to run on all cameras in the scene except for defaults. 
> Or add a widget that presents all cameras available in scene and allows the user to choose what cameras to run the operation on...

3. Click apply to reset the cameras clip plane values

### Camaera Manipulator display
Maya has a handy feature to display a manipulator visualising the near and far clip planes for a camera
<img src="https://user-images.githubusercontent.com/7044060/94469013-556d9f80-0193-11eb-892c-c73b0816cccd.png" width="400" />


The toolbox provides options
- Show or hide the manipulator for cameras
- The camera context to run on can either be on "Selection" or on "All" cameras in the scene
<img src="https://user-images.githubusercontent.com/7044060/94469129-8fd73c80-0193-11eb-8527-febac1c591fa.png" />

