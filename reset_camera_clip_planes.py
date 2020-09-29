# coding=utf-8
"""
Tool to handle the reset camera/s clipping plane in Maya.

This has been tested to run in Windows Maya2019.
"""

__VERSION__ = "0.0.3"

# TODOS:
# - TODO: Refactor code into separate modules...
# - TODO: Cleanup stylesheet
# - TODO: Add callback of camera selection to update a widget displaying the cameras the user has selected

from collections import namedtuple
from collections import OrderedDict
from functools import wraps
import logging
import sys

# Type hinting in PyCharm
try:
    from typing import Callable, Float, Generator, Iterable, Int, Str, Union
except ImportError:
    pass

# Maya imports
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import maya.cmds as mc
# Implementing pymel for convenience of OOP paradigm
# TODO: Should remove pymel due to the slow initialization of the first pymel.core import...
import pymel.core.general as pm_general
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

# Convenience object for containing  near and far clip plane values
ClipPair = namedtuple("ClipPair", "near far")


class NothingSelectedError(Exception):
    pass


class FailedToResolveFromSelectionError(Exception):
    pass


# TODO: Move Maya utils into it's own module...

# --- Maya Utility Functions

def maya_main_window():
    # type: () -> QWidget
    """
    Return the Maya main window widget as a Python object

    :return: The Main Maya Window.
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QWidget)


def is_node_of_type(node, node_type):
    # type: (nt.DagNode, str) -> bool
    """
    Return bool comparison if "node" is of "node type".

    :param node: The node to compare.
    :param node_type: The "node type" to compare with.

    :return: If node is of type.

    """
    return mc.nodeType(str(node)) == node_type


def _in_view_msg_info(msg):
    prefix = "<span style=\"color:green;\">Info: </span>"
    msg = prefix + msg
    mc.inViewMessage(assistMessage=msg, pos='topRight', fade=True, fontSize=8)


def _in_view_msg_warn(msg):
    prefix = "<span style=\"color:#F05A5A;\">Warning: </span>"
    msg = prefix + msg
    mc.inViewMessage(assistMessage=msg, pos='topRight', fade=True, fontSize=8)


def _in_view_msg_error(msg):
    prefix = "<span style=\"color:red;\">Error: </span>"
    msg = prefix + msg
    mc.inViewMessage(assistMessage=msg, pos='topRight', fade=True, fontSize=8)


# --- Maya Camera Functions

def camera_manip_clipping_toggle(cameras, enable=True):
    # type: (Iterable[nt.Camera], bool) -> None
    """
    Function to toggle the visibility of the defined cameras "clipping planes"
    visibility.

    https://help.autodesk.com/view/MAYAUL/2020/ENU/?guid=__PyMel_generated_functions_pymel_core_rendering_pymel_core_rendering_renderManip_html

    :param cameras: Cameras to toggle the manipulator visibility.
    :param enable: True, show the manipulators. False, hide manipulators.

    :return: None

    """
    # sets the visibility of the camera component manipulator for "clipping planes"
    # ["cycling index", "center of interest", "pivot", "clipping planes", "unused"]
    if enable:
        manipulators_state = [False, False, False, True, False]
    else:
        manipulators_state = [False, False, False, False, False]
    for cam in cameras:
        mc.renderManip(str(cam), e=True, camera=manipulators_state)


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


def set_cameras_clip_plane(cameras, near, far):
    # type: (Iterable[nt.Camera], float, float) -> None
    """
    Set defined cameras clip plane values.

    :param cameras: Cameras to set clip plane values for.
    :param near: Near clip plane value to set.
    :param far: Far clip plane value to set.

    :return: None

    """
    for cam in cameras:  # type: nt.Camera
        cam.setNearClipPlane(near)
        cam.setFarClipPlane(far)


def get_selected_cameras():
    # type: () -> Iterable[nt.Camera]

    sel = pm_general.ls(sl=True)

    # Raise if nothing is selected in scene
    if not sel:
        msg = "Nothing Selected!"
        log.error(msg)
        raise NothingSelectedError(msg)

    cameras = list(resolve_cameras(sel))

    # Raise if unable to resolve cameras from selection
    if not cameras:
        log.error('Selection: "%s"' % sel)
        msg = 'No cameras could be resolved from selection!'
        log.error(msg)
        raise FailedToResolveFromSelectionError(msg)

    return cameras


def get_all_cameras():
    # type: () -> Iterable[nt.Camera]
    return pm_general.ls(cameras=True)


# TODO: Move MayaResetCameraClipPlanes into it's own module...

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
        self.clip_values = ClipPair(near=self.DEFAULT_NEAR, far=self.DEFAULT_FAR)

    def reset_cameras(self):
        # type: () -> None

        cls_name = self.__class__.__name__

        get_cameras_func = self.action_map.get(self.mode)  # type: Callable
        log.debug('get_cameras_func: "%s"' % get_cameras_func.__name__)
        try:
            cameras = list(get_cameras_func())

        except NothingSelectedError as err:
            msg = "[{}] {}".format(cls_name, err.message)
            _in_view_msg_error(msg)
            return
        except FailedToResolveFromSelectionError as err:
            msg = "[{}] {}".format(cls_name, err.message)
            _in_view_msg_error(msg)
            return

        # TODO: Confirm if this is needed to propagate the raise traceback...
        except Exception:
            t, v, tb = sys.exc_info()
            raise t, v, tb

        near = float(self.clip_values.near)
        far = float(self.clip_values.far)

        set_cameras_clip_plane(cameras, near, far)

        log.info(
            'Reset camera clip planes on cameras: %s, '
            'with params: near: %1.2f, far: %1.2f' %
            (cameras, near, far)
        )
        msg = "[{}] reset cameras complete ".format(cls_name)
        _in_view_msg_info(msg)

    # TODO: Add documentation...
    # TODO: Handle if unable to resolve cameras from selection...
    @staticmethod
    def camera_manip_show_selected():
        cameras = get_selected_cameras()
        camera_manip_clipping_toggle(cameras, enable=True)

    @staticmethod
    def camera_manip_hide_selected():
        cameras = get_selected_cameras()
        camera_manip_clipping_toggle(cameras, enable=False)

    @staticmethod
    def camera_manip_show_all():
        cameras = get_all_cameras()
        camera_manip_clipping_toggle(cameras, enable=True)

    @staticmethod
    def camera_manip_hide_all():
        cameras = get_all_cameras()
        camera_manip_clipping_toggle(cameras, enable=False)


# TODO: Move refactor UI behaviour into it's own module...

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
            log.info('Closing previous instance of "%s"' % child_name)
            widget.close()
            widget.deleteLater()


def get_widgets_upstream(widget):
    yield widget

    parent = widget.parent()
    if parent:
        for w in get_widgets_upstream(parent):
            yield w


def set_return_widget_tooltip_from_docstring(func):
    """
    Decorator to inject the function docstring into it's returned object tooltip.

    Assumes that the returning object is of type QtWidgets.QWidget
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        widget = func(*args, **kwargs)
        tooltip = func.func_doc  # type: QtWidgets.QWidget

        widget.setToolTip(tooltip)

        return widget

    return wrapper


# Encapsulate "Reset Camera Clip Planes UI" behaviour as it's own object.
# This is so it can be easily augmented with a different  DCC such as
# Houdini, 3DsMax, etc.
class ResetCameraClipPlanesUI(MayaQWidgetDockableMixin, QWidget):

    _VERSION_ = __VERSION__

    DISPLAY_NAME = 'BI - Reset Camera Clip Planes'
    INTERNAL_NAME = 'ResetCameraClipPlanesUIa'

    WIDTH = 640
    HEIGHT = 160

    ResetCameraClipPlanes = MayaResetCameraClipPlanes
    DEFAULT_NEAR = DEFAULT_CLIP_PLANE_NEAR
    DEFAULT_FAR = DEFAULT_CLIP_PLANE_FAR

    DOCUMENTATION_PATH = "https://github.com/uncojohnco/task-2020-BI/blob/main/README.md"

    def __init__(self, parent=None, *args, **kwargs):

        self.destroy_previous_instance()

        parent = parent or maya_main_window()
        super(ResetCameraClipPlanesUI, self).__init__(parent, *args, **kwargs)

        self.setWindowTitle("{} - v{}".format(self.DISPLAY_NAME, self._VERSION_))
        self.setObjectName(self.INTERNAL_NAME)

        self._actions = self.ResetCameraClipPlanes()

        # Widgets
        self._camera_context_options_grp = None  # type: Union[QtWidgets.QButtonGroup, None]
        self._clip_edit_near = None  # type: Union[QtWidgets.QLineEdit, None]
        self._clip_edit_far = None  # type: Union[QtWidgets.QLineEdit, None]

        self._apply_btn = None  # type: Union[QtWidgets.QPushButton, None]

    @classmethod
    def destroy_previous_instance(cls):

        root = maya_main_window()
        destroy_child_widget(root, cls.INTERNAL_NAME)

    # Build UI behaviour

    @set_return_widget_tooltip_from_docstring
    def _init_ui_clip_edits(self):
        # type: () -> QtWidgets.QWidget
        """
        <nobr>
            <b>Near Clip Plane</b>: Value to set the camera(s) "<i>nearClipPlane</i>"<br>
            <b> Far Clip Plane</b>: Value to set the camera(s) "<i>farClipPlane</i>"
        </nobr>

        """

        # Setup

        grp_box = QtWidgets.QGroupBox("Clip Plane values")

        layout = QtWidgets.QFormLayout()
        layout.setContentsMargins(1, 20, 1, 1)
        layout.setSpacing(2)

        # Build

        validator = QtGui.QDoubleValidator()
        validator.setBottom(0)
        validator.setDecimals(3)

        def _create_line_edit(value):
            line_edit = QtWidgets.QLineEdit(str(value))
            line_edit.setValidator(validator)
            line_edit.setMinimumWidth(100)
            return line_edit

        near_edit = _create_line_edit(self.DEFAULT_NEAR)
        far_edit = _create_line_edit(self.DEFAULT_FAR)

        layout.addRow("Near Clip Plane", near_edit)
        layout.addRow("Far Clip Plane", far_edit)

        # Finally

        self._clip_edit_near = near_edit
        self._clip_edit_far = far_edit

        grp_box.setLayout(layout)

        return grp_box

    @set_return_widget_tooltip_from_docstring
    def _init_ui_camera_context_options(self):
        # type: () -> QtWidgets.QWidget
        """
        <nobr>
            <b>selected</b>: 'If checked, will set <b>selected cameras</b> clip values'<br>
            <b>     all</b>: 'If checked, will set <b>all cameras</b> in the scene clip values'
        </nobr>

        """

        modes = self._actions.action_map.keys()

        # Setup

        grp_box = QtWidgets.QGroupBox("Camera Context")
        layout = QtWidgets.QVBoxLayout()
        # layout.setContentsMargins(1, 1, 1, 1)
        layout.addSpacing(10)
        # Build

        button_grp = QtWidgets.QButtonGroup()

        for ii, mode in enumerate(modes):  # type: Str
            rb = QtWidgets.QRadioButton(mode.capitalize())
            layout.addWidget(rb)
            button_grp.addButton(rb, ii)

        layout.itemAt(1).wid.setChecked(True)
        layout.addSpacing(10)
        # Finally

        self._camera_context_options_grp = button_grp

        grp_box.setLayout(layout)

        return grp_box

    @set_return_widget_tooltip_from_docstring
    def _init_ui_action_buttons(self):
        # type: () -> QtWidgets.QWidget
        """
        <nobr>
            <b>Apply button</b>: Click this button to set the clip plane values
            for the cameras defined by the "Camera Context"
        </nobr>

        """

        # Build

        grp_box = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        apply_btn = QtWidgets.QPushButton("Apply")
        layout.addStretch()
        layout.addWidget(apply_btn)

        # Finally

        self._apply_btn = apply_btn

        grp_box.setLayout(layout)

        return grp_box

    def _init_ui_reset_clip_planes(self):
        # type: () -> QtWidgets.QWidget

        # Compose Widgets

        clip_edit_wgt = self._init_ui_clip_edits()
        camera_context_wgt = self._init_ui_camera_context_options()
        actions_wgt = self._init_ui_action_buttons()

        # Compose Tool Layout

        grp_box = QtWidgets.QGroupBox("Reset Camera Clip Planes")
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 20, 5, 5)
        layout.setSpacing(1)
        grp_box.setLayout(layout)

        layout.addWidget(clip_edit_wgt)
        layout.addWidget(camera_context_wgt)
        layout.addWidget(actions_wgt)

        # Compose connections

        self._apply_btn.clicked.connect(self._reset_cameras_clip_planes)

        return grp_box

    # TODO: Perhaps should have implemented QMainWindow...
    def _init_ui_menubar(self):
        # type: () -> QtWidgets.QMenuBar()

        menu_bar = QtWidgets.QMenuBar()

        action_reset_ui = QtWidgets.QAction("Reset UI", self)
        action_open_doc = QtWidgets.QAction("Open Documentation", self)

        menu_bar.addAction(action_reset_ui)
        menu_bar.addAction(action_open_doc)

        action_reset_ui.triggered.connect(self._reset_ui)
        action_open_doc.triggered.connect(self._open_help)

        return menu_bar

    @set_return_widget_tooltip_from_docstring
    def _init_ui_toolbar(self):
        # type: () -> QtWidgets.QToolBar()
        """
        <nobr>
            Tools to toggle the visibility of the Camera clip planes manipulators
            for the selected cameras.
        </nobr>

        """

        grp_box = QtWidgets.QGroupBox("Camera manip")
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(5, 20, 5, 5)

        # TODO: Change these into icons...
        action_show_clip_manip = QtWidgets.QPushButton("show sel", self)
        action_hide_clip_manip = QtWidgets.QPushButton("hide sel", self)
        action_show_clip_manip_all = QtWidgets.QPushButton("show all", self)
        action_hide_clip_manip_all = QtWidgets.QPushButton("hide all", self)

        action_show_clip_manip.setToolTip("Show the camera clip planes manipulator for selected cameras")
        action_hide_clip_manip.setToolTip("Hide the camera clip planes manipulator for selected cameras")
        action_show_clip_manip.setToolTip("Show the camera clip planes manipulator for all cameras")
        action_hide_clip_manip.setToolTip("Hide the camera clip planes manipulator for all cameras")

        layout.addWidget(action_show_clip_manip, 0, 0)
        layout.addWidget(action_hide_clip_manip, 1, 0)

        layout.addWidget(action_show_clip_manip_all, 0, 1)
        layout.addWidget(action_hide_clip_manip_all, 1, 1)

        action_show_clip_manip.clicked.connect(self._camera_manip_show_selected)
        action_hide_clip_manip.clicked.connect(self._camera_manip_hide_selected)
        action_show_clip_manip_all.clicked.connect(self._camera_manip_show_all)
        action_hide_clip_manip_all.clicked.connect(self._camera_manip_hide_all)

        grp_box.setLayout(layout)

        return grp_box

    def _init_ui(self):
        # type: () -> QtWidgets.QLayout()

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setMargin(2)
        main_layout.setSpacing(2)

        menu_bar = self._init_ui_menubar()

        # Tools Section
        set_clip_planes_grpbox = self._init_ui_reset_clip_planes()
        tool_bar = self._init_ui_toolbar()

        tools_layout = QtWidgets.QHBoxLayout()
        tools_layout.addWidget(set_clip_planes_grpbox)
        tools_layout.addWidget(tool_bar)

        line = QtWidgets.QFrame()
        line.setFixedHeight(1)
        line.setFrameShape(QtWidgets.QFrame.HLine)

        menu_bar.setFixedHeight(30)

        main_layout.addWidget(menu_bar)
        main_layout.addWidget(line)
        main_layout.addLayout(tools_layout)

        self.setLayout(main_layout)

        return main_layout

    # Primary entry method

    def display(self):

        self._init_ui()

        control = "{}WorkspaceControl".format(self.INTERNAL_NAME)
        if mc.workspaceControl(control, q=True, exists=True):
            mc.workspaceControl(control, e=True, close=True)
            mc.deleteUI(control, control=True)

        self.show(dockable=True, floating=True)

        # TODO: A proper style sheet should be implemented...
        # TODO: Improve QGroupBox margins...
        self.setStyleSheet(
            "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; font-size:10pt }"
            # TODO: not sure why font weight isn't being set for the title...
            "QGroupBox::title { background-color: transparent; font-weight: bold; color: grey }"
            "QGroupBox { padding: 2px 5px; border-width: 1px; border-style: solid; }"
            # TODO: reduce sie of buttons
            # "QPushButton { margin 0px; padding 0px 20px; border-width: 1px; }"
        )

        # last item is MayaWindow. The child of MayaWindow
        # is the widget we want to resize
        parent_widgets = list(get_widgets_upstream(tool_ui))
        parent_widgets[-2].setFixedSize(tool_ui.WIDTH, tool_ui.HEIGHT)

        log.info('Display of UI complete')

    # UI Actions commands

    def _reset_ui(self):

        self._clip_edit_near.setText(str(self.DEFAULT_NEAR))
        self._clip_edit_far.setText(str(self.DEFAULT_FAR))

    def _reset_cameras_clip_planes(self):

        camera_actions = self._actions

        def _get_mode():
            btn_grp = self._camera_context_options_grp
            mode_id = btn_grp.checkedId()
            return camera_actions.action_map.keys()[mode_id]

        def _get_clip_values():
            near = float(self._clip_edit_near.text())
            far = float(self._clip_edit_far.text())
            return ClipPair(near, far)

        mode = _get_mode()
        clip_values = _get_clip_values()

        log.debug('Camera context resolved from UI: "%s", "%s"' % (mode, clip_values))

        camera_actions.mode = mode
        camera_actions.clip_values = clip_values
        camera_actions.reset_cameras()

    def _camera_manip_show_selected(self):
        self._actions.camera_manip_show_selected()

    def _camera_manip_hide_selected(self):
        self._actions.camera_manip_hide_selected()

    def _camera_manip_show_all(self):
        self._actions.camera_manip_show_all()

    def _camera_manip_hide_all(self):
        self._actions.camera_manip_hide_all()

    def _open_help(self):

        import webbrowser
        webbrowser.open(self.DOCUMENTATION_PATH)


# TODO: Move into util module...
# https://stackoverflow.com/questions/1343227/can-pythons-logging-format-be-modified-depending-on-the-message-log-level
class CustomFormatter(logging.Formatter):

    err_fmt = "[%(name)s] %(levelname)s: %(msg)s"
    dbg_fmt = "[%(name)s] %(levelname)s: %(pathname)s.%(lineno)d: %(msg)s"
    info_fmt = "[%(name)s] %(levelname)s: %(msg)s"

    def __init__(self, fmt="%(levelno)s: %(msg)s"):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):

        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = CustomFormatter.dbg_fmt

        elif record.levelno == logging.INFO:
            self._fmt = CustomFormatter.info_fmt

        elif record.levelno == logging.ERROR:
            self._fmt = CustomFormatter.err_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result


if __name__ == "__main__":

    import maya.utils

    # Setting the name of the logger if we are in the "__main__" frame of Maya
    log = logging.getLogger("reset_camera_clip_planes")
    log.propagate = False

    log_level = logging.DEBUG
    # log_level = logging.INFO

    if not log.handlers:
        handler = maya.utils.MayaGuiLogHandler()
        log.addHandler(handler)
    else:
        handler = log.handlers[0]

    formatter = CustomFormatter()
    handler.setFormatter(formatter)

    log.setLevel(log_level)

    tool_ui = ResetCameraClipPlanesUI()
    # Delay to make sure pymel has been imported...
    QtCore.QTimer.singleShot(100, tool_ui.display)
