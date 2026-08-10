"""
DROBaseWidget
-------------

"""

import os
from enum import IntEnum

from PySide6.QtCore import Slot, Property

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.settings import getSetting

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger

from qtpyvcp.utilities.info import Info

IN_DESIGNER = os.getenv('DESIGNER', False)
LOG = logger.getLogger(__name__)
INFO = Info()

# Set once the undeclared-G7 config error below has been reported, so it lands
# in the log without every X DRO repeating it on every modal change.
_WARNED_UNDECLARED_LATHE = False


class Axis(IntEnum):
    ALL = -1
    X, Y, Z, A, B, C, U, V, W = list(range(9))


class Units(IntEnum):
    Program = 0  # Auto based on G20/G21
    Inch = 1     # Always show inch units
    Metric = 2   # Always show metric units


class RefType(IntEnum):
    Absolute = 0      # Relative to G53
    Relative = 1      # Relative to current WCS
    DistanceToGo = 2  # Remaining distance of the current move


class LatheMode(IntEnum):
    Auto = 0      # Auto based on G7/G8
    Radius = 1    # Always show radius
    Diameter = 2  # Always show diameter


class DROBaseWidget(VCPWidget):
    """DROBaseWidget

    This class implements the basic functionality needed for DRO widgets.
    """

    def __init__(self):
        # PySide6's QWidget bases chain cooperatively through the MRO, so
        # DROLabel/DROLineEdit's `super().__init__(parent)` already reaches
        # this body before their explicit DROBaseWidget.__init__(self) call
        # runs it a second time. That doubled every subscription made below.
        # Guard rather than drop the explicit call, which is still what makes
        # this run at all if a subclass's chain does not reach us.
        if getattr(self, '_dro_base_ready', False):
            return
        self._dro_base_ready = True

        super(DROBaseWidget, self).__init__()

        # Channels this widget has already connected to, so the deliberate
        # overlap between __init__ and initialize() cannot stack up duplicates.
        self._subscribed = set()
        # The single position channel this DRO listens to, and the handle that
        # lets it stop listening when referenceType changes.
        self._pos_channel = None
        self._pos_handle = None

        self.status = getPlugin('status')
        self.pos = getPlugin('position')

        self._anum = Axis.X
        self._ref_typ = RefType.Relative
        self._mm_fmt = '%10.3f'
        self._in_fmt = '%9.4f'
        self._deg_fmt = '%10.2f' #'%(deg) %(min)\' %(sec)"'

        self._use_global_fmt_settings = True

        # settings
        self.in_fmt_setting = None
        self.mm_fmt_setting = None
        self.deg_fmt_setting = None
        self.lathe_mode_setting = None

        self._angular_axis = False

        # lathe
        self._is_lathe = INFO.getIsLathe()
        self._g7_active = False
        self._lathe_mode = LatheMode.Auto  # latheDiameterMode

        self._fmt = self._in_fmt
        self._input_type = 'number:float'

        if IN_DESIGNER:
            return
        
        # Calling updateValue here under pyside is causing
        # super not called errors.
        #self.updateValue()

        self._subscribeOnce(self.status.program_units, self.updateUnits, 'string')

        # Wire position change signals immediately; initialize() is sometimes
        # bypassed in designer-loaded widgets under Qt6/PySide6.
        self._connectPositionChannel()

        if self._is_lathe:
            # Seed from the current modal state before subscribing. gcodes only
            # emits on *change*, and widgets loaded from the config dir are
            # often built after the startup code has already applied G7, so
            # waiting for a notification leaves them showing radius forever.
            self._g7_active = 'G7' in (self.status.gcodes.getValue() or ())
            self._subscribeOnce(self.status.gcodes, self.updateDiameterMode)

            if self._anum == Axis.X:
                # No Qt calls here (no objectName(), no setText()): QUiLoader is
                # still constructing this widget and touching the QObject from
                # __init__ segfaults PySide6.
                LOG.info("LATHE-DRO seed: class=%s axis=X lathe_mode=%s "
                         "g7_flag=%s gcodes=[%s]",
                         self.__class__.__name__,
                         getattr(self._lathe_mode, 'name', self._lathe_mode),
                         self._g7_active,
                         " ".join(self.status.gcodes.getValue() or ()))

        elif self._anum == Axis.X:
            # No lathe flag in the INI, so none of the G7 handling above runs
            # -- but the interpreter halves every X word regardless while G7 is
            # active. Watch for that pairing and say so, rather than quietly
            # showing the operator half of what they typed.
            self._subscribeOnce(self.status.gcodes, self.checkUndeclaredLatheG7)
            self.checkUndeclaredLatheG7(self.status.gcodes.getValue())

        if self._use_global_fmt_settings:

            self.in_fmt_setting = getSetting('dro.inch-format')
            self.mm_fmt_setting = getSetting('dro.millimeter-format')
            self.deg_fmt_setting = getSetting('dro.degree-format')
            self.lathe_mode_setting = getSetting('dro.lathe-radius-mode')

            try:
                self._subscribeOnce(self.in_fmt_setting, self.setInchFormat)
                self._subscribeOnce(self.mm_fmt_setting, self.setMillimeterFormat)
                self._subscribeOnce(self.deg_fmt_setting, self.setDegreeFormat)
                self._subscribeOnce(self.lathe_mode_setting, self.setLatheMode)

            except AttributeError:  # settings not found
                pass

    def _subscribeOnce(self, channel, slot, *args):
        """Connect `slot` to `channel`, at most once for this widget.

        __init__ and initialize() deliberately wire the same channels, and
        neither can be dropped: getSetting() can still return None during
        construction, while initialize() is skipped for some designer-loaded
        widgets under PySide6. So track what is already connected instead.
        """
        # Not repr(slot): this runs mid-construction, where repr() on a
        # half-built QObject raises "base class __init__ not called".
        key = (channel, getattr(slot, '__name__', None) or id(slot))
        if key in self._subscribed:
            return
        channel.notify(slot, *args)     # raises AttributeError if channel is None
        self._subscribed.add(key)

    def _connectPositionChannel(self):
        """Listen to exactly the position channel `referenceType` names.

        Designer properties are applied after construction, so a DRO has to
        subscribe once under the default RefType before it is ever told what
        it displays. The position plugin emits rel, abs and dtg on every poll,
        so a leftover subscription is not harmless: the DRO would repaint with
        another reference type's value before its own. Drop the previous
        connection before making the new one, which also makes repeated
        __init__/initialize()/property writes idempotent.
        """
        channel = getattr(self.pos, self._ref_typ.name)
        if self._pos_channel is channel and self._pos_handle is not None:
            return
        if self._pos_handle is not None:
            self._pos_channel.unnotify(self._pos_handle)
        self._pos_channel = channel
        self._pos_handle = channel.notify(self.updateValue)

    def updateUnits(self, units=None):
        """Force update of DRO display units.

        Args:
            units (str) : Display unis, either `in` or `mm`. Optional
                If no unit type is specified the current program units will
                be used.
        """

        if self._angular_axis:
            self._fmt = self._deg_fmt

        else:
            if IN_DESIGNER:
                self._fmt = self._mm_fmt
                return
            if units is None:
                units = str(self.status.program_units)

            if units == 'in':
                self._fmt = self._in_fmt
            else:
                self._fmt = self._mm_fmt

        # force update
        self.updateValue()

    def initialize(self):
        if self._is_lathe:
            # Re-seed before the first updateValue(): the modal state can have
            # changed between construction and initialization.
            self._g7_active = 'G7' in (self.status.gcodes.getValue() or ())

        self._connectPositionChannel()
        self.updateValue()
        LOG.info(
            "DRO initialized axis=%s ref=%s value=%s",
            getattr(self._anum, 'name', self._anum),
            getattr(self._ref_typ, 'name', self._ref_typ),
            getattr(self.pos, self._ref_typ.name).getValue()[self._anum],
        )

        if self._is_lathe:
            self._subscribeOnce(self.status.gcodes, self.updateDiameterMode)

        if self._use_global_fmt_settings:

            self.in_fmt_setting = getSetting('dro.inch-format')
            self.mm_fmt_setting = getSetting('dro.millimeter-format')
            self.deg_fmt_setting = getSetting('dro.degree-format')
            self.lathe_mode_setting = getSetting('dro.lathe-radius-mode')

            try:
                self._subscribeOnce(self.in_fmt_setting, self.setInchFormat)
                self._subscribeOnce(self.mm_fmt_setting, self.setMillimeterFormat)
                self._subscribeOnce(self.deg_fmt_setting, self.setDegreeFormat)
                self._subscribeOnce(self.lathe_mode_setting, self.setLatheMode)

            except AttributeError:  # settings not found
                pass

    def latheG7Actual(self):
        """Whether the interpreter reports G7 (diameter mode) right now."""
        try:
            return 'G7' in (self.status.gcodes.getValue() or ())
        except Exception:
            return False

    def latheG7Mismatch(self):
        """True when this widget's cached G7 flag disagrees with the interpreter.

        That disagreement is the bug: LinuxCNC halves every X word while G7 is
        active, so a DRO that does not know about G7 shows (and accepts) radius
        where the operator means diameter.
        """
        return self._is_lathe and self._g7_active != self.latheG7Actual()

    def latheUndeclaredG7(self):
        """True when the interpreter is in G7 but the INI declares no lathe.

        LinuxCNC's own GUIs gate their diameter handling on the INI exactly as
        this widget does -- see the `lathe` check in axis.py's touch off prompt
        and gmoccapy's `if self.lathe_mode:` around its G7/G8 test. So this
        combination is a config error, not a gating error: the INI needs
        [DISPLAY]LATHE, and until it has it nothing here converts X.
        """
        return not self._is_lathe and self.latheG7Actual()

    def checkUndeclaredLatheG7(self, gcodes):
        """Warn once per session when G7 turns up in a non-lathe config.

        Subscribed for the X DRO only, and only where the INI declares no
        lathe -- the one case the rest of this class cannot compensate for.
        """
        global _WARNED_UNDECLARED_LATHE
        if _WARNED_UNDECLARED_LATHE or self._is_lathe:
            return
        if 'G7' not in (gcodes or ()):
            return
        _WARNED_UNDECLARED_LATHE = True
        self.warnUndeclaredLatheG7()

    def warnUndeclaredLatheG7(self, entered=None, sent=None):
        """Spell out the INI error behind a silently halved X DRO.

        Safe to call during construction -- it touches no Qt state.
        """
        LOG.warning("bgred<==== G7 DIAMETER MODE, BUT NO LATHE IN THE INI ====>")
        if entered is not None:
            LOG.warning("bgred<LATHE-DRO> typed=%s sent=%s", entered, sent)
        LOG.warning("bgred<LATHE-DRO> The interpreter is in G7 (diameter "
                    "mode), but neither LATHE nor BACK_TOOL_LATHE is set in "
                    "the INI [DISPLAY] section, so the DROs run as a mill and "
                    "never convert X.")
        LOG.warning("bgred<LATHE-DRO> The X DRO reads radius while the machine "
                    "works in diameter: type 20 and it reads back 10. The "
                    "stored offset itself is correct.")
        LOG.warning("bgred<LATHE-DRO> Fix the INI: add 'LATHE = 1' under "
                    "[DISPLAY], plus 'BACK_TOOL_LATHE = 1' as well for a back "
                    "tool post machine.")

    def latheStateSummary(self):
        """One-line diameter/radius state, for troubleshooting logs.

        Only call this after construction -- it touches the QObject.
        """
        try:
            gcodes = self.status.gcodes.getValue() or ()
        except Exception:
            gcodes = ()
        try:
            name = self.objectName() or self.__class__.__name__
        except Exception:
            name = self.__class__.__name__
        try:
            axis = 'XYZABCUVW'[self._anum]
        except (IndexError, TypeError):
            axis = str(self._anum)
        return (
            "widget=%s axis=%s lathe_mode=%s g7_flag=%s g7_actual=%s gcodes=[%s]"
            % (name,
               axis,
               getattr(self._lathe_mode, 'name', self._lathe_mode),
               self._g7_active,
               'G7' in gcodes,
               " ".join(gcodes))
        )

    def updateDiameterMode(self, gcodes):
        was = self._g7_active
        self._g7_active = 'G7' in gcodes
        if was != self._g7_active and self._anum == Axis.X:
            LOG.info("LATHE-DRO g7 changed %s->%s: %s",
                     was, self._g7_active, self.latheStateSummary())
        self.updateValue()

    def updateValue(self, pos=None):
        """Update the displayed position."""
        if IN_DESIGNER:
            return
        if pos is None:
            pos = getattr(self.pos, self._ref_typ.name).getValue()

        if self._is_lathe and self._anum == Axis.X:
            if self._lathe_mode == LatheMode.Diameter or \
                    (self._lathe_mode == LatheMode.Auto and self._g7_active):
                self.setText(self._fmt % (pos[self._anum] * 2))
            else:
                self.setText(self._fmt % pos[self._anum])

        else:
            self.setText(self._fmt % pos[self._anum])



    @Property(int)
    def referenceType(self):
        return self._ref_typ

    @referenceType.setter
    def referenceType(self, ref_type):
        # Rewire to the newly requested reference source (abs/rel/dtg).
        self._ref_typ = RefType(ref_type)
        self._connectPositionChannel()
        self.updateValue()

    @Property(int)
    def axisNumber(self):
        return self._anum

    @axisNumber.setter
    def axisNumber(self, axis):
        self._anum = axis
        if axis in [3, 4, 5]:
            self._angular_axis = True
            self._fmt = self._deg_fmt
        self.updateValue()

    @Property(str)
    def inchFormat(self):
        return self._in_fmt

    @inchFormat.setter
    def inchFormat(self, in_fmt):
        if in_fmt == '' and self.mm_fmt_setting:
            self.in_fmt_setting.resetValue()

        else:
            try:
                txt = in_fmt % 360.42
                self._in_fmt = in_fmt
            except:
                if self.in_fmt_setting:
                    self.in_fmt_setting.setValue(self._in_fmt)

        self.updateUnits()

    @Slot(str)
    @Slot(object)
    def setInchFormat(self, fmt):
        self.inchFormat = fmt

    @Property(str)
    def millimeterFormat(self):
        return self._mm_fmt

    @millimeterFormat.setter
    def millimeterFormat(self, mm_fmt):
        if mm_fmt == '' and self.mm_fmt_setting:
            self.mm_fmt_setting.resetValue()

        else:
            try:
                txt = mm_fmt % 360.42
                self._mm_fmt = mm_fmt
            except:
                if self.mm_fmt_setting:
                    self.mm_fmt_setting.setValue(self._mm_fmt)

        self.updateUnits()

    @Slot(str)
    @Slot(object)
    def setMillimeterFormat(self, fmt):
        self.millimeterFormat = fmt

    # ToDO: Add support for DMS angle notation
    # https://stackoverflow.com/questions/2579535
    @Property(str)
    def degreeFormat(self):
        return self._deg_fmt

    @degreeFormat.setter
    def degreeFormat(self, deg_fmt):

        if deg_fmt == '' and self.deg_fmt_setting:
            self.deg_fmt_setting.resetValue()

        else:
            try:
                txt = deg_fmt % 360.42
                self._deg_fmt = deg_fmt
            except:
                if self.deg_fmt_setting:
                    self.deg_fmt_setting.setValue(self._deg_fmt)

        self.updateUnits()

    @Slot(str)
    @Slot(object)
    def setDegreeFormat(self, fmt):
        self.degreeFormat = fmt

    @Property(bool)
    def useGlobalDroFormatSettings(self):
        return self._use_global_fmt_settings

    @useGlobalDroFormatSettings.setter
    def useGlobalDroFormatSettings(self, use_fmt_settings):
        self._use_global_fmt_settings = use_fmt_settings

    @Property(int)
    def latheMode(self):
        return self._lathe_mode

    @latheMode.setter
    def latheMode(self, mode):
        self._lathe_mode = LatheMode(mode)
        self.updateValue()

    @Property(str)
    def inputType(self):
        return self._input_type

    @inputType.setter
    def inputType(self, input_type):
        self._input_type = input_type

    @Slot(int)
    @Slot(object)
    def setLatheMode(self, mode):
        self.latheMode = LatheMode(mode)

    @Slot()
    def latheDiameterMode(self):
        self.latheMode = LatheMode.Diameter

    @Slot()
    def latheRadiusMode(self):
        self.latheMode = LatheMode.Radius

    @Slot()
    def latheAutoMode(self):
        self.latheMode = LatheMode.Auto
