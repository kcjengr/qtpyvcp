from PySide6.QtCore import Slot
from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow
from PySide6.QtWidgets import QWidget

# Setup logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger('qtpyvcp.' + __name__)

class MyMainWindow(VCPMainWindow):
    """Main window class for the VCP."""
    def __init__(self, *args, **kwargs):
        super(MyMainWindow, self).__init__(*args, **kwargs)
        # Replace placeholder VTKBackPlot with real runtime version
        self._replace_vtk_placeholder()

    def _replace_vtk_placeholder(self):
        """Replace designer placeholder with real VTK widget at runtime."""
        try:
            # Import the real VTKBackPlot first
            from qtpyvcp.widgets.display_widgets.vtk_backplot import VTKBackPlot as RealVTKBackPlot
            from PySide6.QtWidgets import QGridLayout, QBoxLayout
            
            # Find the placeholder VTKBackPlot widget by name
            placeholder = self.findChild(QWidget, "vtkbackplot")
            
            if placeholder is not None:
                LOG.info("Found VTKBackPlot placeholder, replacing with real widget...")
                
                # Create real widget
                real_vtk = RealVTKBackPlot()
                real_vtk.setObjectName("vtkbackplot")
                
                # Get parent and layout
                parent = placeholder.parent()
                if parent is None:
                    LOG.warning("Placeholder has no parent, cannot replace")
                    return
                
                layout = parent.layout()
                if layout is None:
                    LOG.warning("Parent has no layout, cannot replace")
                    return
                
                # Handle different layout types
                if isinstance(layout, QGridLayout):
                    # For QGridLayout, get the position of the placeholder
                    index = layout.indexOf(placeholder)
                    if index < 0:
                        LOG.warning("Placeholder not found in layout")
                        return
                    
                    # Get row and column
                    pos = layout.getItemPosition(index)
                    if pos:
                        row, col, rowSpan, colSpan = pos
                        layout.removeWidget(placeholder)
                        layout.addWidget(real_vtk, row, col, rowSpan, colSpan)
                        LOG.info(f"Replaced in QGridLayout at row {row}, col {col}")
                    else:
                        LOG.warning("Could not get position from QGridLayout")
                        
                elif isinstance(layout, QBoxLayout):
                    # For QBoxLayout, use insertWidget
                    index = layout.indexOf(placeholder)
                    if index >= 0:
                        layout.removeWidget(placeholder)
                        layout.insertWidget(index, real_vtk)
                        LOG.info(f"Replaced in QBoxLayout at index {index}")
                    else:
                        LOG.warning("Placeholder not found in layout")
                else:
                    # Generic fallback
                    LOG.warning(f"Unknown layout type: {type(layout)}")
                    layout.removeWidget(placeholder)
                    layout.addWidget(real_vtk)
                
                # Delete placeholder
                placeholder.deleteLater()
                
                LOG.info("Successfully replaced VTKBackPlot placeholder with real VTK widget")
            else:
                LOG.warning("Could not find VTKBackPlot placeholder widget")
                
        except ImportError as e:
            LOG.warning(f"VTK not available, using placeholder: {e}")
        except Exception as e:
            LOG.exception(f"Error replacing VTK placeholder: {e}")

    # add any custom methods here
    @Slot()
    def on_exitBtn_clicked(self):
        self.app.quit()

