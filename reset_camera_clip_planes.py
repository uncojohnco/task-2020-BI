"""
Tool to handle the reset camera/s clipping plane in Maya.

This has been tested to run in Windows Maya2019.
"""

from collections import namedtuple
from collections import OrderedDict
import logging

# Type hinting in PyCharm
try:
    from typing import Callable, Float, Generator, Iterable, Str
except ImportError:
    pass

# Maya imports
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import maya.cmds as mc
import pymel.core as pm
import pymel.core.nodetypes as nt

# Qt imports
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance


log = logging.getLogger(__name__)

QWidget = QtWidgets.QWidget


DEFAULT_CLIP_PLANE_NEAR = 1.0
DEFAULT_CLIP_PLANE_FAR = 50000.0

ClipPair = namedtuple("ClipPair", "near far")


# --- UI Utility Functions

def maya_main_window():
    # type: () -> QWidget
    """
    Return the Maya main window widget as a Python object

    :return: The Main Maya Window.
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QWidget)


def destroy_child_widget(parent, child_name):
    # type: (QWidget, str) -> None
    """
    Destroy a child widget of the specified parent widget.

    :param parent: Parent widget to resolve child widgets from.
    :param child_name: Name of the child widget to destroy.

    :return: None

    """
    for widget in parent.children():  # type: QWidget

        if widget.objectName() == child_name:
            log.info('Closing previous instance of "%s"', child_name)
            widget.close()
            widget.deleteLater()


# --- Maya Utility Functions

def is_node_of_type(node, node_type):
    # type: (nt.DagNode, str) -> bool
    """
    Return bool comparison if "node" is of "node type".

    :param node: The node to compare.
    :param node_type: The "node type" to compare with.

    :return: If node is of type.

    """
    return node.type() == node_type


# --- Camera Functions

def resolve_cameras(nodes):
    # type: (Iterable[nt.DagNode]) -> Generator[nt.Camera]
    """
    From the sequence of nodes, return nodes that are of a "Camera Type".

    :param nodes: Sequence of nodes to filter.

    :return: Nodes that are of "Camera Type".

    """
    for node in nodes:
        if is_node_of_type(node, "transform"):
            for cam in node.listRelatives(type="camera"):
                yield cam

        elif is_node_of_type(node, "camera"):
            yield node


def reset_cameras_clip_plane(cameras, near, far):
    # type: (Iterable[nt.Camera], float, float) -> None
    """
    Reset defined cameras clip plane values.

    :param cameras: Cameras to reset clip plane values.
    :param near: Near clip plane value to set.
    :param far: Far clip plane value to set.

    :return: None

    """
    for cam in cameras:  # type: nt.Camera
        cam.setNearClipPlane(near)
        cam.setFarClipPlane(far)


def get_selected_cameras():
    # type: () -> Iterable[nt.Camera]
    return resolve_cameras(pm.ls(sl=True))


def get_all_cameras():
    # type: () -> Iterable[nt.Camera]
    return pm.ls(cameras=True)


# Encapsulate "Maya Reset Camera Clip Planes" behaviour as it's own object.
# This is so it can be easily augmented with a different UI Frame work.
class MayaResetCameraClipPlanes(object):
    """
    Class to handle resetting cameras clip planes in a Maya scene.

    Attributes
    ----------
    action_map: Dict
        Used to resolve the set of cameras to reset depending
        on the "mode" value which is used as the key.

    mode: Str
        Property to define which cameras to resolve for "self.get_cameras()".

    clip_values: ClipPair
        The values to set the near and far clip planes for the camera(s).
    """

    # Map to resolve which set of cameras will be acted upon.
    action_map = OrderedDict()
    action_map["selected"] = get_selected_cameras
    action_map["all"] = get_all_cameras

    DEFAULT_NEAR = DEFAULT_CLIP_PLANE_NEAR
    DEFAULT_FAR = DEFAULT_CLIP_PLANE_FAR

    def __int__(self):

        self.mode = self.action_map.keys()[0]  # type: Str
        self.clip_values = ClipPair(self.DEFAULT_NEAR, self.DEFAULT_FAR)

    def get_cameras(self):
        # type: () -> Iterable[nt.Camera]
        """
        Resolves a set of cameras depending on the value of the "self.mode".

        :return: A set of cameras.
        """

        get_cameras_func = self.action_map.get(self.mode)  # type: Callable
        logging.debug('get_cameras_func: "%s"', get_cameras_func)

        return get_cameras_func()

    def reset_cameras(self):
        # type: () -> None

        cameras = list(self.get_cameras())
        if not cameras:
            logging.warning("No cameras were resolved")
            return

        near, far = self.clip_values  # type: ClipPair
        logging.debug(
            'Reset camera clip planes on cameras: %s, '
            'with params: near: %f, far: %f',
            cameras, near, far
        )

        reset_cameras_clip_plane(cameras, near, far)


# Encapsulate "Reset Camera Clip Planes UI" behaviour as it's own object.
# This is so it can be easily augmented with a different  DCC such as
# Houdini, 3DsMax, etc.
class ResetCameraClipPlanesUI(MayaQWidgetDockableMixin, QWidget):

    DISPLAY_NAME = 'BI - Reset Camera Clip Planes'
    INTERNAL_NAME = 'ResetCameraClipPlanesUIa'

    WIDTH = 450
    HEIGHT = 600

    ResetCameraClipPlanes = MayaResetCameraClipPlanes
    DEFAULT_NEAR = DEFAULT_CLIP_PLANE_NEAR
    DEFAULT_FAR = DEFAULT_CLIP_PLANE_FAR

    def __init__(self, *args, **kwargs):

        self._action = self.ResetCameraClipPlanes()

        self.destroy_previous_instance()

        super(ResetCameraClipPlanesUI, self).__init__(*args, **kwargs)

        self.setWindowTitle(self.DISPLAY_NAME)
        self.setObjectName(self.INTERNAL_NAME)

        self.resize(self.WIDTH, self.HEIGHT)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # Widgets
        self._camera_context_options_grp = None  # type: QtWidgets.QButtonGroup

        self._near_edit = None  # type: QtWidgets.QLineEdit
        self._far_edit = None  # type: QtWidgets.QLineEdit

        self._apply_btn = None  # type: QtWidgets.QPushButton

    def _init_ui_clip_edits(self):
        # type: () -> (QtWidgets.QButtonGroup, QtWidgets.QGroupBox)

        def _create_line_edit(value):
            line_edit = QtWidgets.QLineEdit(str(value))
            line_edit.setValidator(validator)
            line_edit.setMinimumWidth(200)
            return line_edit

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(1, 1, 1, 1)

        validator = QtGui.QDoubleValidator()
        validator.setBottom(0)
        validator.setDecimals(3)

        near_edit = _create_line_edit(self.DEFAULT_NEAR)
        far_edit = _create_line_edit(self.DEFAULT_FAR)

        layout.addRow("Near Clip Plane", near_edit)
        layout.addRow("Far Clip Plane", far_edit)

        return near_edit, far_edit, layout

    def _init_ui_camera_context_options(self):
        # type: () -> (QtWidgets.QButtonGroup, QtWidgets.QGroupBox)

        modes = self._action.action_map.keys()

        button_grp = QtWidgets.QButtonGroup()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)

        for ii, mode in enumerate(modes):  # type: Str
            rb = QtWidgets.QRadioButton(mode.capitalize())
            layout.addWidget(rb)
            button_grp.addButton(rb, ii)
        layout.addStretch()

        layout.itemAt(0).wid.setChecked(True)

        return button_grp, layout

    def _init_ui_apply_button(self):

        apply_btn = QtWidgets.QPushButton("Apply")

        layout = QtWidgets.QVBoxLayout()
        layout.addStretch()
        layout.addWidget(apply_btn)

        return apply_btn, layout

    def _init_ui(self):

        # Setup Widgets

        camera_context_btn_grp, camera_context_lyt = self._init_ui_camera_context_options()
        near_edit, far_edit, clip_edit_lyt = self._init_ui_clip_edits()
        apply_btn, apply_btn_layout = self._init_ui_apply_button()

        # Setup Main Layout

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)

        clip_edit_grp_box = QtWidgets.QGroupBox("Reset Values")
        clip_edit_grp_box.setLayout(clip_edit_lyt)

        camera_context_grp_box = QtWidgets.QGroupBox("Camera Context")
        camera_context_grp_box.setLayout(camera_context_lyt)

        main_layout.addWidget(clip_edit_grp_box)
        main_layout.addWidget(camera_context_grp_box)
        main_layout.addLayout(apply_btn_layout)

        apply_btn.clicked.connect(self.apply_button_clicked)

        self._camera_context_options_grp = camera_context_btn_grp
        self._near_edit = near_edit
        self._far_edit = far_edit
        self._apply_btn = apply_btn

    def apply_button_clicked(self):

        reset_cameras = self._action

        def _get_mode():
            btn_grp = self._camera_context_options_grp
            mode_id = btn_grp.checkedId()
            return reset_cameras.action_map.keys()[mode_id]

        def _get_clip_values():
            return ClipPair(float(self._near_edit.text()), float(self._far_edit.text()))

        mode = _get_mode()
        clip_values = _get_clip_values()

        log.debug('Camera context resolved from UI: "%s"', mode)
        log.debug(': "%s"', clip_values)

        reset_cameras.mode = mode
        reset_cameras.clip_values = clip_values
        reset_cameras.reset_cameras()

    def display(self):

        self._init_ui()

        # https://discourse.techart.online/t/mayas-dockableworkspacewidget-py-and-deleting-the-ui-upon-closing-maya/10664
        control = "{}WorkspaceControl".format(self.INTERNAL_NAME)
        if mc.workspaceControl(control, q=True, exists=True):
            mc.workspaceControl(control,e=True, close=True)
            mc.deleteUI(control, control=True)

        self.show(dockable=True, floating=True)

    @classmethod
    def destroy_previous_instance(cls):

        root = maya_main_window()
        destroy_child_widget(root, cls.INTERNAL_NAME)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    tool_ui = ResetCameraClipPlanesUI()
    tool_ui.display()
