from functools import partial

def setupNav(parent):
    parent.probetabGroup.buttonClicked.connect(partial(probetabChangePage, parent))
    if button.property('buttonName'):
        getattr(parent, button.property('buttonName')).setChecked(True)

