try:
    from shiboken6 import isValid as _is_qobject_valid
except Exception:
    _is_qobject_valid = None


def safe_qt_callback(widget, callback):
    def _wrapped(*args, **kwargs):
        try:
            if _is_qobject_valid is not None and widget is not None and not _is_qobject_valid(widget):
                return
            try:
                callback(*args, **kwargs)
            except TypeError:
                callback()
        except RuntimeError:
            return

    return _wrapped
