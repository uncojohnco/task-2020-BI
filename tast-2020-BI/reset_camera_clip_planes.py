"""
Tool to handle the reset camera/s clipping plane in Maya.
"""

try:
    from typing import List, Generator, Sequence
except ImportError:
    pass

import pymel.core as pm
import pymel.core.nodetypes as nt


# --- Utility Functions

def is_node_of_type(n, node_type):
    # type: (nt.DagNode, str) -> bool
    return n.type() == node_type


# --- Camera Functions

def resolve_cameras(nodes):
    # type: (List[nt.DagNode])  -> Generator[nt.Camera]

    for node in nodes:
        if is_node_of_type(node, "transform"):
            for cam in node.listRelatives(type="camera"):
                yield cam

        elif is_node_of_type(node, "camera"):
            yield node


def reset_cameras_clip_plane(cameras, near, far):
    # type: (Sequence[nt.Camera], float, float) -> None

    for cam in cameras:  # type: nt.Camera
        cam.setNearClipPlane(near)
        cam.setFarClipPlane(far)


def reset_cameras_clip_plane_all(near, far):
    # type: (float, float) -> None

    cameras = pm.ls(cameras=True)
    reset_cameras_clip_plane(cameras, near, far)


# --- UI

