# Widgets Test Sim Configuration

## Overview

This is a comprehensive test platform for QtPyVCP custom widgets with PySide6.
It contains all 49+ custom widgets in a single UI for testing, development, and verification.

## Features

- **Complete Widget Test**: All QtPyVCP button, display, input, HAL, and form widgets
- **PySide6 Compatible**: Tests the migration from PyQt5 to PySide6
- **LinuxCNC Integration**: Can be launched as a full LinuxCNC VCP
- **Simulation Environment**: Includes simulated 3-axis XYZ machine

## How to Launch

### From LinuxCNC Launcher
1. Open the LinuxCNC Launcher
2. Browse to the Widgets Test Sim configuration
3. Click "Run" to launch the VCP

### From Command Line
```bash
cd ~/linuxcnc
linuxcnc ~/Dev/qtpyvcp/configs/widgets_test_sim/widgets_test_sim.ini
```

Or using qtvcp directly:
```bash
cd ~/Dev/qtpyvcp/configs/widgets_test_sim
qtvcp -c custom_config.yml
```

## Files

- **widgets_test_sim.ini** - LinuxCNC configuration file
- **custom_config.yml** - QtPyVCP YAML configuration
- **mainwindow.ui** - Qt Designer UI file with all widgets
- **style.qss** - Custom stylesheet
- **core_sim.hal** - HAL simulation components
- **sim_spindle_encoder.hal** - Spindle simulation
- **postgui.hal** - Post-GUI HAL configuration
- **shutdown.hal** - Shutdown sequence
- **sim.var** - NC parameter file
- **subroutines/** - O-word subroutines directory

## Testing

This configuration allows testing:
- Widget loading in Qt Designer
- PySide6 compatibility of all custom widgets
- Visual layout and styling
- Real-time updates with LinuxCNC data
- HAL pin connections and status display

## Notes

- The machine is simulated with no real hardware
- All axes default to home position at 0,0,0
- No tool table or ATC configuration
- Contains test data for all widget types
