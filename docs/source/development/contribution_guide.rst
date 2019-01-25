Contribution Guide
^^^^^^^^^^^^^^^^^^

There are many ways to contribute to QtPyVCP, and all are encouraged and
greatly appreciated:

- contributing bug reports and feature requests

- contributing documentation (and yes that includes this document)

- reviewing and triaging any bugs and merge requests

- testing and providing feedback on problems / bugs

Before you go any further, be reassured that your contribution, however slight,
*is* valuable. Even if it is something as simple as fixing a spelling error,
or clarifying a sentence in the docs.


Guidelines
==========

We don't have any strict guidlines, you are encouraged to contribute
in whatever way you are capable of, and most importantly, have fun
and hopefully learn something in the process. That being said, bellow
are a few recommendations that should make it easier for all evolved.


Development Workflow
====================

In general we try to use the *Feature Branch and Merge requests* workflow.
If you are not familiar with git workflows don't worry, it's very straight
forward (and we are not strict about it anyway).


Commit Messages
===============

While by no means required, it is nice if you prefix commit messages
with a TLA (Three Letter Acronym) indicating the commit type. This makes
it easy to visually scan the commit log and see what types of changes
were made. It also makes it possible to grep for specific commit types.
For example, to view all BugFix commits you can use ``git log --grep=BUG``.
Maybe most importantly, commit prefixes are used to auto-generate change
logs for each release.

===  ===
TLA  Description
===  ===
API   an (incompatible) API change
BLD   change related to building
BUG   bug fix
DEP   deprecate something, or remove a deprecated object
DEV   development tool or utility
DOC   documentation
ENH   enhancement
MNT   maintenance commit (refactoring, typos, etc.)
REV   revert an earlier commit
STY   style fix (whitespace, PEP8)
TST   addition or modification of tests
REL   related to a release (increment version numbers etc.)
WIP   work in progress
SIM   change related to linuxcnc sim configs
VCP   work on example VCPs
===  ===

With that in mind, an ideal commit message might look something like this:

.. code-block:: none

  DOC: add example commit message to development guidelines (See #42)

  The first line of a commit message should start with a capitalized acronym
  (options in table above) indicating the commit type, and a short summary.
  If the commit is related to a GitHub issue, then indicate that with
  "Fixes #42", "See #42", "Closes #42" or similar.

  If this is not enough to fully describe the commit, then add a blank line
  and more text as needed. Lines shouldn't be longer than 72 characters so
  they display well when viewing the git log in a terminal.

Do we live in an ideal world? No. It's fine if your commit messages vary
from this format, but you should at least try to use TLAs for commits you
would like to show up on in the change logs.


Python Docstrings
=================

It is appreciated if you document your code by writing docstrings for all python
modules, classes and functions. These are automatically converted by Sphinx into
HTML documentation. Docstrings should follow the Google style guidelines, example
of which can be found `here
<https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`__.
