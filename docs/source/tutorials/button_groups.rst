=============
Button Groups
=============

Button Groups is a very powerful and flexible way to have a touch screen
keyboard. You add push buttons to the panel then select them all and add them to
a button group.

Once you `connect` the button group to a function when a button is pressed it
sends the button pressed to the function. Then you can use the properties of the
button like `button.text()` to get the text of the button.

For this tutorial I'll clone a copy of the 
`vcp template <https://github.com/kcjengr/vcp-template>`_ by opening a terminal
and using this command. If you already have the vcp template skip this part.
::

    git clone https://github.com/kcjengr/vcp-template.git


In a terminal change to the vcp-template directory and run the tutorial.sh
script with these commands. I named the copy ``button_group`` and copied the
LinuxCNC Configuration Files so I could test the VCP.
::

    cd vcp-template
    ./tutorial.sh

Now open a terminal and edit the vcp with ``editvcp`` and select
`~button_group/button_group/config.yml`.

.. image:: images/btn-grp-designer-01.png
   :align: center
   :scale: 80 %

Now we have the blank template to work with.

.. image:: images/btn-grp-designer-02.png
   :align: center
   :scale: 40 %

Lets start by adding some buttons to create a number keypad. First drag a `Grid
Layout` into the main window and right click on it and morph it into a `Group
Box`. Next drag some buttons into the group box like so.

.. image:: images/btn-grp-designer-03.png
   :align: center
   :scale: 40 %

This is a touch screen example so lets make the buttons big enough to touch. In
the Main Window open the `stylesheet` and add the following style to set the
mininum height and width and set the font size.
::

    QPushButton {
    min-height: 50px;
    min-width: 50px;
    font: 14pt "DejaVu Sans";
    }

.. image:: images/btn-grp-designer-04.png
   :align: center
   :scale: 40 %

Now we can see the buttons are large enough to use with a touch screen.

.. image:: images/btn-grp-designer-05.png
   :align: center
   :scale: 40 %

Next we need to add the buttons into a group Ctrl left click on each button to
select it then right click on any button and select `Assign to button group`
`New button group`

.. image:: images/btn-grp-designer-06.png
   :align: center
   :scale: 40 %

Change the objectName of the button group to ``numberGroup`` and change the text
of the buttons like this.

.. image:: images/btn-grp-designer-07.png
   :align: center
   :scale: 40 %

Now add a label and stretch it so it spans the width of the group box and change
the objectName to ``displayLabel``. I added a box to the label and changed the
font to alignRight and the font size to 14.

.. image:: images/btn-grp-designer-08.png
   :align: center
   :scale: 40 %

If you run the button group you can see the buttons but they won't do anything.
Open `~button_group/button_group/mainwindow.py` and you will see the following.
::

    from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow

    # Setup logging
    from qtpyvcp.utilities import logger
    LOG = logger.getLogger('qtpyvcp.' + __name__)

    class MyMainWindow(VCPMainWindow):
        """Main window class for the VCP."""
        def __init__(self, *args, **kwargs):
            super(MyMainWindow, self).__init__(*args, **kwargs)

        # add any custom methods here

Indentation in Python is strict so use spaces in this file so they remain the
same. In the `__init__` function we need to connect the button group to a
function. We do this with a `connect` function. We connect the buttonClicked
that is passed by the button group to the function.
::

    self.buttonGroupName.buttonClicked.connect(self.functionName)

So add the following to mainwindow.py.
::

    self.numberGroup.buttonClicked.connect(self.numberKeys)

We also need to create the function `numberKeys` and for now it will do nothing.
::

    def numberKeys(self, button):
        pass
