# LinuxCNC Var File Monitoring System

## Overview

This system provides real-time monitoring and synchronization of LinuxCNC parameter (var) files with QtPyVCP widgets. It enables widgets to automatically update when external processes modify var file parameters, eliminating stale data issues.

## Architecture

The system consists of four main components:

### 1. VarFileManager Plugin (`plugins/var_file_manager.py`)
- **Purpose**: Centralized var file monitoring and management
- **Features**:
  - Automatic var file detection from LinuxCNC configuration
  - Real-time file monitoring using QFileSystemWatcher
  - Parameter caching and change detection
  - Widget subscription system for targeted updates
  - Configurable monitoring modes (filesystem watching or polling)

### 2. VarWidgetMixin (`widgets/base_widgets/var_widget_mixin.py`)
- **Purpose**: Reusable base class for widgets that monitor var parameters
- **Features**:
  - Automatic registration with VarFileManager
  - Abstract methods for parameter loading and value comparison
  - Cleanup management for proper resource disposal
  - Clean fail-fast design with no fallbacks

### 3. Updated Widgets
- **VCPVarLineEdit** (`widgets/input_widgets/var_line_edit.py`)
- **VCPVarPushButton** (`widgets/button_widgets/vcpvar_button.py`)
- Both widgets now use the centralized monitoring system
- Real-time synchronization when var file changes
- Maintains all existing functionality and safety features

### 4. Configuration Integration
- **Default Config** (`yaml_lib/default_config.yml`)
- VarFileManager automatically included in all QtPyVCP applications
- Configurable monitoring options

## Usage

### Basic Widget Setup in Qt Designer

1. **VCPVarLineEdit**:
   ```
   varParameterNumber: 3014  # Parameter to monitor
   autoWriteEnabled: true    # Auto-write changes to var file
   requireHomed: false       # Safety requirement
   ```

2. **VCPVarPushButton**:
   ```
   varParameterNumber: 3014  # Parameter to monitor  
   autoWriteEnabled: true    # Auto-write changes to var file
   outputAsInt: false        # Output format (bool vs int)
   requireHomed: false       # Safety requirement
   ```

### Real-time Synchronization

The system automatically provides:
- **Widget-to-Widget sync**: When one widget changes a parameter, all other widgets monitoring the same parameter update immediately
- **External change sync**: When external processes (G-code, MDI, other tools) modify var files, widgets update automatically
- **Efficient monitoring**: Single file watcher shared across all var widgets

### Configuration Options

Add to your VCP configuration file:

```yaml
data_plugins:
  var_file_manager:
    provider: qtpyvcp.plugins.var_file_manager:VarFileManager
    kwargs:
      # monitoring mode: 'filesystem' (default) or 'polling'
      monitoring_mode: filesystem
      # polling interval in ms (only used if monitoring_mode is 'polling')
      polling_interval: 500
```

## Development Guide

### Creating New Var Widgets

To create a new widget that monitors var file parameters:

1. **Inherit from VarWidgetMixin**:
   ```python
   from qtpyvcp.widgets.base_widgets.var_widget_mixin import VarWidgetMixin
   
   class MyVarWidget(QWidget, VCPWidget, VarWidgetMixin):
       def __init__(self, parent=None):
           super().__init__(parent)
           VarWidgetMixin.__init__(self)
   ```

2. **Implement Abstract Methods**:
   ```python
   def _load_parameter_value(self, value):
       """Load parameter value from var file into widget"""
       # Update your widget's display with the new value
       pass
   
   def _get_widget_value(self):
       """Get current widget value for comparison"""
       # Return the current widget value as float
       return float(self.current_value)
   ```

3. **Initialize and Cleanup**:
   ```python
   def initialize(self):
       self._initialize_var_monitoring()
       # Your other initialization code
   
   def terminate(self):
       self._cleanup_var_monitoring()
       # Your other cleanup code
   ```

4. **Add Property for Qt Designer**:
   ```python
   @Property(int)
   def varParameterNumber(self):
       return self.var_parameter_number
   
   @varParameterNumber.setter 
   def varParameterNumber(self, param_num):
       self.var_parameter_number = int(param_num)
   ```

### Code Quality Standards

The system follows strict code quality standards:
- **No fallbacks**: Fail fast on errors rather than silent degradation
- **No try blocks**: Clean predictable code flow
- **Explicit error handling**: Clear error messages and logging
- **Resource management**: Proper initialization and cleanup

## Testing

### Standalone Tests
```bash
cd src/qtpyvcp
python test_var_widgets/standalone_tests.py
```

### Test Application
```bash
cd src/qtpyvcp/test_var_widgets
python test_app.py
```

The test application demonstrates:
- Real-time synchronization between line edit and push button widgets
- External file modification detection
- Multiple parameter monitoring

## API Reference

### VarFileManager Methods
- `get_parameter_value(param_num)`: Get current parameter value
- `subscribe_to_parameter(param_num, callback)`: Subscribe to parameter changes
- `unsubscribe_from_parameter(param_num, callback)`: Unsubscribe from changes

### VarWidgetMixin Properties
- `var_parameter_number`: Parameter number to monitor (int)
- `var_monitoring_enabled`: Whether monitoring is active (bool, read-only)
- `var_file_manager`: Reference to the VarFileManager plugin (read-only)

### Widget Properties (Qt Designer)
- `varParameterNumber`: Parameter number to monitor
- `autoWriteEnabled`: Enable automatic writing to var file
- `requireHomed`: Require machine to be homed for safety

## Safety Features

- **Machine state validation**: Widgets can require machine to be homed before allowing parameter changes
- **Status plugin integration**: Automatic disable when machine is not in safe state
- **Fail-fast design**: Immediate failure on configuration errors rather than silent malfunction

## Troubleshooting

### Common Issues

1. **Widget not updating**: Check that VarFileManager plugin is loaded in configuration
2. **Parameter not found**: Verify parameter exists in var file and number is correct
3. **Permission errors**: Ensure var file is writable by QtPyVCP process

### Debug Logging

Enable debug logging for detailed monitoring information:

```yaml
data_plugins:
  var_file_manager:
    provider: qtpyvcp.plugins.var_file_manager:VarFileManager
    log_level: debug
```

## Migration from Manual Monitoring

If upgrading existing var widgets:

1. Add `VarWidgetMixin` to inheritance chain
2. Replace manual file reading with `_load_parameter_value()` implementation  
3. Replace manual file monitoring setup with `_initialize_var_monitoring()`
4. Update property references from `_var_parameter_number` to `var_parameter_number`
5. Remove manual file handling code (`readParameterFromVarFile`, etc.)

## Performance

- **Efficient monitoring**: Single file watcher for all widgets
- **Minimal overhead**: Only monitored parameters are cached
- **Change detection**: Updates only occur when values actually change
- **Background operation**: File monitoring doesn't block UI
