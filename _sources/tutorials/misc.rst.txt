=============
Tips & Tricks
=============

Exit Application Button
***********************

In the mainwindow.py file add the following code
::

  def on_exitAppBtn_clicked(self):
    self.app.quit()

In the designer add a normal `Push Button` and set the objectName to
`exitAppBtn`
