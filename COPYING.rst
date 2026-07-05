Terms and Conditions
========================================================================

The QtPyVCP project contains code with separate copyright notices
and license terms.  As a whole QtPyVCP may be redistributed and/or
modified in accordance with the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License, or
(at your option) any later version, subject to the QtPyVCP
Free-Standing Module Exception described below.  Individual files may
be licensed under
less strict terms and conditions and can be distributed subject to the
terms and conditions set forth in the file header.

All files distributed as part of QtPyVCP are assumed to be covered by
the GPLv2 License unless stated otherwise in the file header.

Each license is included in its entirety in the LICENSES directory.

------------------------------------------------------------------------
Free-Standing Module Exception
------------------------------------------------------------------------

As a special exception, the copyright holders of QtPyVCP grant
permission to combine QtPyVCP, or a VCP based on QtPyVCP, with
free-standing modules that use QtPyVCP's published Python APIs solely
for integration, regardless of the license terms of those modules, and
to copy and distribute such modules under terms of your choice,
including alongside QtPyVCP or a VCP, provided they remain separate
works.

This exception is narrow by design.  It covers modules with
substantial functionality of their own -- for example conversational
programming, CAM, probing, or nesting tools -- that plug into QtPyVCP
or a VCP for display and data exchange but do not depend on QtPyVCP
for their core function and do not alter the behavior of QtPyVCP
itself.  Such modules must be distributed on their own, separately
from QtPyVCP and from any VCP, and may only supplement a VCP that is
fully functional for its intended purpose without them: a VCP may not
rely on such a module, or any combination of such modules, to provide
its essential functionality.  Modules meeting these conditions may be
released under any license, including proprietary (closed-source)
licenses.

It does not cover VCPs, widget or dialog libraries built to extend
QtPyVCP, modified versions of bundled plugins or widgets, or anything
that incorporates QtPyVCP source code -- all of which remain covered
by the GPL, as does QtPyVCP itself.

The full text of the exception, including the five-part definition of
a "qualifying free-standing module", is in
LICENSES/GPL-Free-Standing-Module-Exception.md.  Note that the exception does not
cover third-party components such as PyQt or the LinuxCNC libraries;
users of the exception must comply with those licenses separately.

------------------------------------------------------------------------
Components provided under additional licenses
------------------------------------------------------------------------

Some self-contained python modules are covered by the MIT License (to
make reuse in other non GPL projects easier).

Code adapted from PyDM is covered by the BSD 3-Clause License.

Images and icons are covered by the CC Attribution-ShareAlike License.


Links
-----
PyDM (https://github.com/slaclab/pydm)
