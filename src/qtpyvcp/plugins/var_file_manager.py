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
Var File Manager Plugin

This plugin provides centralized monitoring and management of LinuxCNC parameter 
(var) file changes. It allows widgets to subscribe to specific parameter changes
and automatically updates them when the var file is modified by external sources
like G-code execution or manual MDI commands.

Features:
- Automatic var file path detection from LinuxCNC ini configuration
- Real-time file monitoring using QFileSystemWatcher
- Intelligent change detection (only notifies for actually changed parameters)
- Widget subscription system for parameter-specific notifications
- Parameter value caching for performance
- Handles file deletion/recreation edge cases
- Clean fail-fast error handling with no fallbacks
"""

import os
from collections import defaultdict

from qtpy.QtCore import QFileSystemWatcher, QTimer, Signal

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin

LOG = getLogger(__name__)
INFO = Info()


class VarFileManager(DataPlugin):
    """
    Centralized LinuxCNC parameter file manager and monitor.
    
    This plugin provides a centralized system for monitoring LinuxCNC var file
    changes and notifying subscribed widgets when their parameters change.
    """
    
    # Signals for widget communication
    parameter_changed = Signal(int, object)  # (param_number, new_value)
    parameters_changed = Signal(dict)        # {param_number: new_value, ...}
    file_reloaded = Signal()                 # Emitted after file reload completes
    file_error = Signal(str)                 # Emitted on file access errors
    
    def __init__(self, update_delay=50, cache_size=1000, auto_register=True, 
                 monitoring_mode='filesystem', polling_interval=500):
        """
        Initialize the VarFileManager plugin.
        
        Args:
            update_delay (int): Delay in ms before processing parameter updates
            cache_size (int): Maximum number of parameters to cache
            auto_register (bool): Whether to automatically register with plugin system
            monitoring_mode (str): Monitoring mode - 'filesystem' or 'polling'
            polling_interval (int): Polling interval in ms (used if monitoring_mode is 'polling')
        """
        super(VarFileManager, self).__init__()
        
        # Configuration
        self._update_delay = update_delay
        self._cache_size = cache_size
        self._auto_register = auto_register
        self._monitoring_mode = monitoring_mode
        self._polling_interval = polling_interval
        
        # File monitoring
        self._parameter_file_path = None
        self._fs_watcher = None
        self._polling_timer = None
        self._reload_timer = None
        
        # Parameter management
        self._parameter_cache = {}  # {param_number: value}
        self._last_file_mtime = None
        
        # Widget subscription system
        self._widget_subscriptions = defaultdict(set)  # {param_number: {widgets}}
        self._widget_to_params = defaultdict(set)      # {widget: {param_numbers}}
        
        # Initialize parameter file path detection
        self._detect_parameter_file_path()
        
        LOG.info(f"VarFileManager initialized with parameter file: {self._parameter_file_path}")

    def _detect_parameter_file_path(self):
        """Detect the LinuxCNC parameter file path from ini configuration"""
        parameter_file = INFO.getParameterFile()
        if not parameter_file:
            LOG.error("VarFileManager: No parameter file found in LinuxCNC configuration")
            return
            
        # Handle relative paths
        if not os.path.isabs(parameter_file):
            config_dir = os.getenv('CONFIG_DIR', '.')
            self._parameter_file_path = os.path.join(config_dir, parameter_file)
        else:
            self._parameter_file_path = parameter_file
            
        if not os.path.exists(self._parameter_file_path):
            LOG.error(f"VarFileManager: Parameter file does not exist: {self._parameter_file_path}")
            self._parameter_file_path = None
            return
            
        LOG.debug(f"VarFileManager: Detected parameter file path: {self._parameter_file_path}")

    def initialise(self):
        """Initialize the plugin - called by QtPyVCP framework"""
        if not self._parameter_file_path:
            LOG.error("VarFileManager: Cannot initialize - no valid parameter file path")
            return
            
        # Setup monitoring based on mode
        if self._monitoring_mode == 'filesystem':
            # Setup file system watcher
            self._fs_watcher = QFileSystemWatcher([self._parameter_file_path])
            self._fs_watcher.fileChanged.connect(self._on_file_changed)
            LOG.info(f"VarFileManager: Using filesystem monitoring on {self._parameter_file_path}")
            
            # Also set up backup polling every 1 second as fallback
            self._polling_timer = QTimer()
            self._polling_timer.timeout.connect(self._poll_file_changes)
            self._polling_timer.start(1000)  # Check every 1 second as backup
            LOG.debug("VarFileManager: Added backup polling every 1 second")
            
        elif self._monitoring_mode == 'polling':
            # Setup polling timer
            self._polling_timer = QTimer()
            self._polling_timer.timeout.connect(self._poll_file_changes)
            self._polling_timer.start(self._polling_interval)
            LOG.info(f"VarFileManager: Using polling monitoring every {self._polling_interval}ms")
        else:
            LOG.warning(f"VarFileManager: Unknown monitoring mode '{self._monitoring_mode}', using filesystem")
            self._fs_watcher = QFileSystemWatcher([self._parameter_file_path])
            self._fs_watcher.fileChanged.connect(self._on_file_changed)
        
        # Setup reload timer for handling file write completion
        self._reload_timer = QTimer()
        self._reload_timer.setSingleShot(True)
        self._reload_timer.timeout.connect(self._process_file_change)
        
        # Load initial parameter values
        self._load_parameter_cache()
        
        LOG.info("VarFileManager: File monitoring initialized")
        self._initialized = True

    def terminate(self):
        """Cleanup when plugin is destroyed"""
        if self._reload_timer and self._reload_timer.isActive():
            self._reload_timer.stop()
            
        if self._polling_timer and self._polling_timer.isActive():
            self._polling_timer.stop()
            
        if self._fs_watcher:
            self._fs_watcher.deleteLater()
            
        # Clear all subscriptions
        self._widget_subscriptions.clear()
        self._widget_to_params.clear()
        self._parameter_cache.clear()
        
        LOG.debug("VarFileManager: Cleanup completed")

    # Widget Registration API
    def register_widget(self, widget, param_number):
        """
        Register a widget to receive notifications for a specific parameter.
        
        Args:
            widget: The widget object to register
            param_number (int): LinuxCNC parameter number to monitor
        """
        if not isinstance(param_number, int) or param_number < 0:
            LOG.error(f"VarFileManager: Invalid parameter number: {param_number}")
            return
            
        self._widget_subscriptions[param_number].add(widget)
        self._widget_to_params[widget].add(param_number)
        
        LOG.debug(f"VarFileManager: Registered widget {widget} for parameter #{param_number}")
        
        # If we have a cached value, notify the widget immediately
        if param_number in self._parameter_cache:
            self._notify_widget(widget, param_number, self._parameter_cache[param_number])

    def unregister_widget(self, widget, param_number=None):
        """
        Unregister a widget from parameter notifications.
        
        Args:
            widget: The widget object to unregister
            param_number (int, optional): Specific parameter to unregister from.
                                        If None, unregisters from all parameters.
        """
        if param_number is not None:
            # Unregister from specific parameter
            self._widget_subscriptions[param_number].discard(widget)
            self._widget_to_params[widget].discard(param_number)
            LOG.debug(f"VarFileManager: Unregistered widget {widget} from parameter #{param_number}")
        else:
            # Unregister from all parameters
            params_to_remove = list(self._widget_to_params[widget])
            for param_num in params_to_remove:
                self._widget_subscriptions[param_num].discard(widget)
            self._widget_to_params[widget].clear()
            LOG.debug(f"VarFileManager: Unregistered widget {widget} from all parameters")

    # Parameter Management API
    def get_parameter_value(self, param_number):
        """
        Get the current cached value of a parameter.
        
        Args:
            param_number (int): LinuxCNC parameter number
            
        Returns:
            float or None: Parameter value, or None if not found
        """
        return self._parameter_cache.get(param_number)

    def get_all_parameters(self):
        """
        Get a copy of all cached parameter values.
        
        Returns:
            dict: {param_number: value, ...}
        """
        return self._parameter_cache.copy()

    def refresh_parameter(self, param_number):
        """
        Force refresh a specific parameter from the var file.
        
        Args:
            param_number (int): Parameter number to refresh
        """
        if not self._parameter_file_path or not os.path.exists(self._parameter_file_path):
            LOG.warning("VarFileManager: Cannot refresh parameter - var file not available")
            return
            
        try:
            with open(self._parameter_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                file_param_num = int(parts[0])
                                if file_param_num == param_number:
                                    value = float(parts[1])
                                    old_value = self._parameter_cache.get(param_number)
                                    if old_value != value:
                                        self._parameter_cache[param_number] = value
                                        self._notify_parameter_change(param_number, value)
                                    return
                            except (ValueError, IndexError):
                                continue
        except IOError as e:
            LOG.error(f"VarFileManager: Error reading parameter file: {e}")

    # File Monitoring Implementation
    def _on_file_changed(self, path):
        """Handle file system watcher notification"""
        LOG.debug(f"VarFileManager: Parameter file changed: {path}")
        LOG.debug(f"VarFileManager: Current subscriptions: {list(self._widget_subscriptions.keys())}")
        
        # Use timer to delay processing to handle file write completion
        self._reload_timer.stop()
        self._reload_timer.start(self._update_delay)

    def _process_file_change(self):
        """Process the file change after delay"""
        if not self._parameter_file_path or not os.path.exists(self._parameter_file_path):
            LOG.warning("VarFileManager: Parameter file no longer exists, attempting to re-watch")
            self._re_watch_file()
            return
            
        try:
            # Check if file has actually been modified
            current_mtime = os.path.getmtime(self._parameter_file_path)
            if self._last_file_mtime is not None and current_mtime == self._last_file_mtime:
                LOG.debug("VarFileManager: File timestamp unchanged, skipping reload")
                return
                
            LOG.debug(f"VarFileManager: Processing parameter file changes (mtime: {current_mtime})")
            old_parameters = self._parameter_cache.copy()
            
            # Reload parameter cache
            self._load_parameter_cache()
            
            # Detect and notify changes
            self._detect_and_notify_changes(old_parameters, self._parameter_cache)
            
            # Emit general file reloaded signal
            self.file_reloaded.emit()
            
        except Exception as e:
            LOG.error(f"VarFileManager: Error processing file change: {e}")
            self.file_error.emit(str(e))

    def _poll_file_changes(self):
        """Poll for file changes (used when monitoring_mode is 'polling')"""
        if not self._parameter_file_path or not os.path.exists(self._parameter_file_path):
            LOG.warning("VarFileManager: Parameter file no longer exists during polling")
            return
            
        try:
            # Check if file has been modified since last check
            current_mtime = os.path.getmtime(self._parameter_file_path)
            if self._last_file_mtime is None:
                self._last_file_mtime = current_mtime
                return
                
            if current_mtime != self._last_file_mtime:
                LOG.debug("VarFileManager: File change detected via polling")
                self._process_file_change()
                
        except Exception as e:
            LOG.error(f"VarFileManager: Error during file polling: {e}")

    def _re_watch_file(self):
        """Re-establish file watching if file was deleted and recreated"""
        if self._parameter_file_path and os.path.exists(self._parameter_file_path):
            if self._parameter_file_path not in self._fs_watcher.files():
                self._fs_watcher.addPath(self._parameter_file_path)
                LOG.debug("VarFileManager: Re-established file watching")

    def _load_parameter_cache(self):
        """Load all parameters from var file into cache"""
        if not self._parameter_file_path or not os.path.exists(self._parameter_file_path):
            return
            
        new_cache = {}
        
        try:
            with open(self._parameter_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                param_number = int(parts[0])
                                value = float(parts[1])
                                new_cache[param_number] = value
                            except (ValueError, IndexError):
                                continue
                                
            self._parameter_cache = new_cache
            self._last_file_mtime = os.path.getmtime(self._parameter_file_path)
            
            LOG.debug(f"VarFileManager: Loaded {len(new_cache)} parameters from var file")
            
        except IOError as e:
            LOG.error(f"VarFileManager: Error reading parameter file: {e}")
            self.file_error.emit(str(e))

    def _detect_and_notify_changes(self, old_params, new_params):
        """
        Compare parameter sets and notify widgets of changes.
        
        Args:
            old_params (dict): Previous parameter values
            new_params (dict): Current parameter values
        """
        changes = {}
        
        LOG.debug(f"VarFileManager: Checking changes - old: {len(old_params)}, new: {len(new_params)} parameters")
        
        # Check for changed values
        for param_number, new_value in new_params.items():
            old_value = old_params.get(param_number)
            if old_value != new_value:
                changes[param_number] = new_value
                LOG.debug(f"VarFileManager: Parameter #{param_number} changed: {old_value} -> {new_value}")
                self._notify_parameter_change(param_number, new_value)
                
        # Check for deleted parameters
        for param_number in old_params:
            if param_number not in new_params:
                changes[param_number] = None
                LOG.debug(f"VarFileManager: Parameter #{param_number} deleted")
                self._notify_parameter_change(param_number, None)
                
        if changes:
            LOG.debug(f"VarFileManager: Detected changes in {len(changes)} parameters: {list(changes.keys())}")
            self.parameters_changed.emit(changes)
        else:
            LOG.debug("VarFileManager: No parameter changes detected")

    def _notify_parameter_change(self, param_number, new_value):
        """
        Notify all subscribed widgets of a parameter change.
        
        Args:
            param_number (int): Parameter number that changed
            new_value: New parameter value
        """
        # Emit general parameter change signal
        self.parameter_changed.emit(param_number, new_value)
        
        # Notify specific widgets
        subscribed_widgets = self._widget_subscriptions.get(param_number, set())
        LOG.debug(f"VarFileManager: Notifying {len(subscribed_widgets)} widgets for parameter #{param_number}")
        
        for widget in subscribed_widgets:
            self._notify_widget(widget, param_number, new_value)

    def _notify_widget(self, widget, param_number, value):
        """
        Notify a specific widget of a parameter change.
        
        Args:
            widget: Widget to notify
            param_number (int): Parameter number
            value: Parameter value
        """
        try:
            # Check if widget has the expected notification method
            if hasattr(widget, '_on_parameter_changed'):
                widget._on_parameter_changed(param_number, value)
            else:
                LOG.warning(f"VarFileManager: Widget {widget} does not implement _on_parameter_changed method")
        except Exception as e:
            LOG.error(f"VarFileManager: Error notifying widget {widget}: {e}")

    # DataChannel for plugin status
    @DataChannel
    def file_path(self, chan):
        """Current parameter file path"""
        return self._parameter_file_path

    @DataChannel 
    def is_monitoring(self, chan):
        """Whether file monitoring is active"""
        return self._fs_watcher is not None and len(self._fs_watcher.files()) > 0

    @DataChannel
    def parameter_count(self, chan):
        """Number of cached parameters"""
        return len(self._parameter_cache)

    @DataChannel
    def widget_count(self, chan):
        """Number of registered widgets"""
        return len(self._widget_to_params)

    def __str__(self):
        return f"VarFileManager(file={self._parameter_file_path}, params={len(self._parameter_cache)}, widgets={len(self._widget_to_params)})"
