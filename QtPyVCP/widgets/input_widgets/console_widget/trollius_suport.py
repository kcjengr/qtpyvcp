# -*- coding: utf-8 -*-
import trollius

class QTrolliusEventLoop(trollius.unix_events._UnixSelectorEventLoop):
    def __init__(self, selector=None, app = None):
        super(QTrolliusEventLoop, self).__init__(selector)
        self._app = app

    def _run_once(self):
        super(QTrolliusEventLoop, self)._run_once()

        if self._app:
            self._app.processEvents()
