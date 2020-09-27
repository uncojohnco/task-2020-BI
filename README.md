## Summary

Maya UI Tool to set the scenes camera(s) clip plane values.

## Usage

1. Download this repo
2. copy `reset_camera_clip_planes.py` into:
   - **Windows**: `$HOME/maya/scripts`
3. From a `Python shell` in the `Maya Script Editor`, execute the below:
    - **Windows**:
     ```
    import os
    
    script_path = "{home}/maya/scripts/reset_camera_clip_planes.py".format(home=os.path.expandvars("$HOME"))
    # e.g. "C:/Users/johnco/Documents/maya/scripts/reset_camera_clip_planes.py"
    execfile(script_path)
    ```
