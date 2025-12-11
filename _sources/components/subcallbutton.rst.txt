===============
Sub Call Button
===============

The `SubCallButton` is used to call subroutines similar to NGCGUI subroutines.
The file format is almost the same.

The way you get information into the subroutine is by having widgets with the
same name as the variable or using a default value for the variable. The file
must be executable and have the same name as the sub/endsub.

You can use a line edit, a spin box or a double spin box to set the values for
the variable.

For example if you had a spin box on the tool change page called `tool_number`
you could have one button to change the tool by getting the value from the
`tool_number` spin box.

`tool_change.ngc`
::

  ; tool change subroutine
  o<tool_change> sub

  #<tool_number> = #1 (=1); set the default to 1

  T#<tool_number> M6 G43

  o<tool_change> endsub

The subroutine must be on the path specificed in the ini file and must be
executable. Put the file name including the .ngc in the `FileName` variable of
the `SubCallButton`.
