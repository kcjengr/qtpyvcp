#!/usr/bin/env python

#   Copyright (c) 2025 QtPyVCP Development Team
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.

"""
Var Widget Mixin

This mixin class provides common functionality for widgets that interact with
LinuxCNC parameter (var) files. It handles automatic registration with the
VarFileManager plugin for real-time parameter monitoring and updates.

Features:
- Automatic registration/unregistration with VarFileManager plugin
- Parameter change notification handling
- Clean fail-fast error handling with no fallbacks
- Abstract methods for widget-specific implementation
"""

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import getPlugin

LOG = getLogger(__name__)


class VarWidgetMixin:
    """
    Mixin class for widgets that monitor LinuxCNC var file parameters.
    
    This mixin provides the common functionality needed for widgets to
    automatically receive notifications when their associated parameters
    change in the var file.
    
    Widgets using this mixin must implement:
    - _load_parameter_value(value): Load a value from var file into widget
    - _get_widget_value(): Return current widget value
    
    Optional methods to override:
    - _on_parameter_changed(param_number, new_value): Custom change handling
    """
    
    def __init__(self):
        """Initialize the var widget mixin"""
        # Var file monitoring properties
        self._var_manager = None
        self._var_parameter_number = 0
        self._var_auto_reload = True
        self._var_monitoring_enabled = False
        
        # Track if we've been registered with the manager
        self._var_registered = False

    def _setup_var_monitoring(self):
        """
        Setup monitoring for the widget's parameter.
        
        This should be called during widget initialization, typically
        in the widget's initialize() method.
        """
        if not self._var_auto_reload or self._var_parameter_number <= 0:
            LOG.debug(f"{self.__class__.__name__}: Var monitoring disabled or invalid parameter number")
            return
            
        # Get the VarFileManager plugin
        self._var_manager = getPlugin('var_file_manager')
        if not self._var_manager:
            LOG.warning(f"{self.__class__.__name__}: VarFileManager plugin not available")
            return
            
        # Register this widget for parameter notifications
        self._var_manager.register_widget(self, self._var_parameter_number)
        self._var_registered = True
        self._var_monitoring_enabled = True
        
        LOG.debug(f"{self.__class__.__name__}: Registered for parameter #{self._var_parameter_number} monitoring")
        
        # Load initial value if available
        initial_value = self._var_manager.get_parameter_value(self._var_parameter_number)
        if initial_value is not None:
            self._load_parameter_value(initial_value)

    def _cleanup_var_monitoring(self):
        """
        Cleanup var file monitoring.
        
        This should be called during widget cleanup, typically
        in the widget's terminate() method.
        """
        if self._var_registered and self._var_manager:
            self._var_manager.unregister_widget(self, self._var_parameter_number)
            self._var_registered = False
            self._var_monitoring_enabled = False
            LOG.debug(f"{self.__class__.__name__}: Unregistered from parameter #{self._var_parameter_number} monitoring")

    def _on_parameter_changed(self, param_number, new_value):
        """
        Handle parameter change notifications from VarFileManager.
        
        This method is called by the VarFileManager when the widget's
        parameter changes in the var file. The default implementation
        loads the new value if it's for our parameter.
        
        Widgets can override this method to implement custom handling.
        
        Args:
            param_number (int): The parameter number that changed
            new_value: The new parameter value (float or None)
        """
        if param_number == self._var_parameter_number:
            if new_value is not None:
                LOG.debug(f"{self.__class__.__name__}: Parameter #{param_number} changed to {new_value}")
                self._load_parameter_value(new_value)
            else:
                LOG.debug(f"{self.__class__.__name__}: Parameter #{param_number} was deleted")
                # Parameter was deleted from var file
                self._handle_parameter_deleted()

    def _handle_parameter_deleted(self):
        """
        Handle the case where the widget's parameter was deleted from var file.
        
        Default implementation does nothing. Widgets can override this
        to provide specific behavior when their parameter is removed.
        """
        pass

    def _refresh_parameter(self):
        """
        Force refresh of the widget's parameter from the var file.
        
        This bypasses the cache and reads directly from the file.
        """
        if self._var_manager and self._var_parameter_number > 0:
            self._var_manager.refresh_parameter(self._var_parameter_number)

    def _get_parameter_value_from_manager(self):
        """
        Get the current cached value of the widget's parameter.
        
        Returns:
            float or None: Parameter value from cache, or None if not available
        """
        if self._var_manager and self._var_parameter_number > 0:
            return self._var_manager.get_parameter_value(self._var_parameter_number)
        return None

    # Abstract methods that widgets must implement
    def _load_parameter_value(self, value):
        """
        Load a parameter value into the widget.
        
        This method must be implemented by the widget to define how
        parameter values from the var file are loaded into the widget's
        display/state.
        
        Args:
            value (float): The parameter value to load
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _load_parameter_value(value) method"
        )

    def _get_widget_value(self):
        """
        Get the current value from the widget.
        
        This method must be implemented by the widget to define how
        the widget's current value is retrieved for writing to var file.
        
        Returns:
            float: The widget's current value
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _get_widget_value() method"
        )

    # Property getters/setters for var monitoring configuration
    @property
    def var_parameter_number(self):
        """Get the LinuxCNC parameter number this widget monitors"""
        return self._var_parameter_number

    @var_parameter_number.setter
    def var_parameter_number(self, param_num):
        """Set the LinuxCNC parameter number this widget monitors"""
        old_param = self._var_parameter_number
        self._var_parameter_number = int(param_num) if param_num else 0
        
        # If monitoring is already enabled, re-register for the new parameter
        if self._var_monitoring_enabled and old_param != self._var_parameter_number:
            if self._var_registered and self._var_manager:
                # Unregister from old parameter
                self._var_manager.unregister_widget(self, old_param)
                
                # Register for new parameter if valid
                if self._var_parameter_number > 0:
                    self._var_manager.register_widget(self, self._var_parameter_number)
                    LOG.debug(f"{self.__class__.__name__}: Re-registered from param #{old_param} to #{self._var_parameter_number}")
                else:
                    self._var_registered = False
                    LOG.debug(f"{self.__class__.__name__}: Unregistered from param #{old_param} (new param invalid)")

    @property
    def var_auto_reload(self):
        """Get whether auto-reload from var file is enabled"""
        return self._var_auto_reload

    @var_auto_reload.setter
    def var_auto_reload(self, enabled):
        """Set whether auto-reload from var file is enabled"""
        self._var_auto_reload = bool(enabled)
        
        # If monitoring state needs to change, update it
        if enabled and not self._var_monitoring_enabled and self._var_parameter_number > 0:
            self._setup_var_monitoring()
        elif not enabled and self._var_monitoring_enabled:
            self._cleanup_var_monitoring()

    @property
    def var_monitoring_enabled(self):
        """Get whether var file monitoring is currently active"""
        return self._var_monitoring_enabled

    def __str__(self):
        return f"{self.__class__.__name__}(param=#{self._var_parameter_number}, monitoring={self._var_monitoring_enabled})"
