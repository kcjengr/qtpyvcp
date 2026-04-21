import os as _os
if not _os.getenv('DESIGNER'):
    # Import as redundant alias to suppress linter warnings
    from .vtk_backplot.vtk_backplot import VTKBackPlot as VTKBackPlot