import os as _os
if not _os.getenv('DESIGNER'):
    from .vtk_backplot.vtk_backplot import VTKBackPlot