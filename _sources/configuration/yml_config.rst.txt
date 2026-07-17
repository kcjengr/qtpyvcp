=================
YAML Config Files
=================

At the heart of every QtPyVCP based VCP is a YAML configuration
file. This file is probably more important than any other, since
it defines how the .ui, .py and .qss files come together to make
a complete VCP.

Multiple configuration files are used from various levels, and
when combined and merged determine the final configuration for
the VCP.

At the lowest level is the ``default_config.yml`` file. This file
is not user editable and is always loaded. It defines the basic
things that must exist for the most basic VCP to function.

At the next level is the VCP specific configuration file. This is
where individual VCPs are defined, and is generally only edited by
a VCP developers. It includes basic info such as the VCP name and author,
as well as what .ui, .py and .qss files to use when loading the VCP.
It is also where VCP specific menus, dialogs etc. are defined.

At the highest level is the machine specific configuration file. This
file is usually located in the config dir along with the INI file. It
is not required but can be used to tweak configurations settings for a
particular machine.

More information about YAML files can be found at 
`Wikipedia <https://en.wikipedia.org/wiki/YAML>`_
