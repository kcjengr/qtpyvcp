"""External Widgets

This module loads custom widgets defined in external packages
so they are available in QtDesigner.
"""
from importlib.metadata import entry_points

from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


def _iter_widget_entry_points():
    """Yield qtpyvcp widget entry points across importlib.metadata variants."""
    eps = entry_points()
    # Python 3.10+: EntryPoints object supports select(group=...)
    if hasattr(eps, 'select'):
        return eps.select(group='qtpyvcp.widgets')
    # Older behavior: dict-like mapping by group
    return eps.get('qtpyvcp.widgets', [])


for entry_point in _iter_widget_entry_points():

    try:
        group_name = entry_point.name
        mod = entry_point.load()

        for name in dir(mod):
            if name.startswith('_'):
                continue

            try:
                plugin_cls = getattr(mod, name)
                plugin_cls.group_name = group_name
                globals()[name] = plugin_cls
            except Exception as e:
                LOG.exception("Error while loading custom widget plugin '%s'.",
                              name, exc_info=e)

    except Exception as e:
        LOG.exception("Error while trying to load custom widget package '%s'.",
                      group_name, exc_info=e)
