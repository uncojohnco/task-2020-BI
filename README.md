## Summary

Maya UI Tool to reset the scenes camera(s) clip plane values.

<img alt="Screenshot of a Reset Camera Clip Planes UI session in Maya" 
src="https://user-images.githubusercontent.com/7044060/94517952-fd688480-01f6-11eb-8e4c-df40fc3dfdf2.gif" width="600" />

## TODOS...
 - Add option to run on all cameras in the scene except for defaults. 
   - Or add a widget that presents all cameras available in scene and allows the user to choose what cameras to run the operation on...
 - Update near and far `QLineEdit`s to `QDoubleSpinBox`
 - If the user presses enter in the near and far widget, this should envoke the "apply"

## Install and displaying the UI

1. Download this repo
2. copy `reset_camera_clip_planes.py` into:
   - **Windows**: `$HOME/maya/scripts`
     e.g. on my instance of Windows it would be`C:/Users/johnco/Documents/maya/scripts`
3. From a `Python Buffer` in the `Maya Script Editor`, execute the below:
   - **Windows**:
   ```python
   import os

   script_path = "{home}/maya/scripts/reset_camera_clip_planes.py".format(home=os.path.expandvars("$HOME"))
   # e.g. "C:/Users/johnco/Documents/maya/scripts/reset_camera_clip_planes.py"
   execfile(script_path)
   ```
<img alt="Screenshot of a Reset Camera Clip Planes UI session in Maya" 
src="https://user-images.githubusercontent.com/7044060/94467554-21917a80-0191-11eb-91fb-a411ea3af11c.png" width="300" />

## Usage

With the tool open...<br>
<img alt="Screenshot of the Reset Camera Clip Planes UI" 
src="https://user-images.githubusercontent.com/7044060/94468728-e728dd00-0192-11eb-90ff-a15252458ff7.png" width="600" />

### Reset Camera Clip Planes Operation

<img src="https://user-images.githubusercontent.com/7044060/94506792-347d6c80-01dc-11eb-84c1-e6de53ea92eb.png" width="400" />
1. Set the clip plane values to desired values

2. Choose the camera context to for the "Apply" operation to execute on.
   - Can either be run on the selected cameras in the scene
   - Or on all cameras

3. Click apply to reset the cameras clip plane values

### Camaera Manipulator display
Maya has a handy feature to display a manipulator visualising the near and far clip planes for a camera
<img alt="Demo of the Maya Camera Clip planes manipulator"
src="https://user-images.githubusercontent.com/7044060/94506216-dac87280-01da-11eb-924b-afe84564aa15.gif" width="400" />


The toolbox provides options
- Show or hide the manipulator for cameras
- The camera context to run on can either be on "Selection" or on "All" cameras in the scene
<img alt="Screenshot of the Camaera Manipulator Tool area"
src="https://user-images.githubusercontent.com/7044060/94506700-0566fb00-01dc-11eb-886d-ff53a3feaeac.png" width="400"/>

