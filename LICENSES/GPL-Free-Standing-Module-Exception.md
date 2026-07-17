# QtPyVCP Free-Standing Module Exception to the GNU GPL

Version 1.0

In addition to the permissions granted by the GNU General Public
License, the copyright holders of QtPyVCP grant you the following
special exception:

As a special exception, the copyright holders of QtPyVCP give you
permission to combine QtPyVCP, or a virtual control panel (VCP) based
on QtPyVCP, with a qualifying free-standing module (as defined below),
regardless of the license terms of that module, and to copy and
distribute the module under terms of your choice for use in
combination with QtPyVCP or with such a VCP.  This includes
distributing the module alongside QtPyVCP or a VCP, provided that the
module remains a separate work as required by condition 4 below, and
that QtPyVCP and the VCP themselves remain subject to, and are
distributed in compliance with, the GNU General Public License.

## Definition of a qualifying free-standing module

A "qualifying free-standing module" is a work that satisfies all five
of the following conditions.  (Such modules are often referred to
informally as plugins; this exception uses "module" to avoid confusion
with the data plugins that are part of QtPyVCP itself.)

1. **Substantial independent function.**  The primary purpose of the
   module is to provide functionality of its own -- for example
   conversational programming, CAM or toolpath generation, probing
   routines, nesting, or tool and job database management -- and not
   to extend, re-implement, or alter the functionality of QtPyVCP
   itself.

2. **Integration-only use of QtPyVCP.**  The module's interaction with
   QtPyVCP is limited to integration through QtPyVCP's published
   Python APIs: embedding the module's user interface in a VCP,
   subclassing the classes QtPyVCP provides for registration and
   extension (such as ``DataPlugin`` and ``DataChannel``), exchanging
   data through plugin channels, and invoking published actions.  The
   module must remain a coherent and substantially functional work if
   this integration layer were removed or replaced.

3. **No modification of QtPyVCP.**  The module is not derived from
   QtPyVCP source code, and does not patch, monkey-patch, replace,
   override, or otherwise alter the behavior of QtPyVCP code or of the
   plugins and widgets distributed with QtPyVCP, at build time or at
   run time.

4. **Separate distribution.**  The module is distributed as a
   separate, self-contained work under its own name and terms, and can
   be installed and removed independently of QtPyVCP and of any VCP.
   The module may not be distributed as an integral part of QtPyVCP or
   of a VCP.  Distributing the module alongside QtPyVCP or a VCP --
   for example preinstalled on a machine -- is permitted, provided the
   module remains a separately identifiable work that can be removed
   without affecting the VCP's essential functionality.

5. **Supplementary functionality only.**  The module only adds to the
   functionality of a VCP that is complete and fully functional for
   its intended purpose without it.  A VCP may not rely on a
   qualifying free-standing module, or on any combination of such
   modules, to provide its essential or primary functionality:
   removing the module, and all other such modules, must leave the VCP
   fully usable for its intended purpose.

   For example, a proprietary module may not be used to provide the
   main functionality of a 3D printer VCP, but could provide an
   embedded slicer, as long as the VCP would be usable without such
   modules installed.

## Works this exception does not cover

For the avoidance of doubt, the following are not qualifying
free-standing modules and remain subject to the GNU General Public
License in full:

- widget, dialog, or component libraries whose primary purpose is to
  extend or supplement QtPyVCP's user interface toolkit;
- modified or replacement versions of the plugins, widgets, or other
  components distributed with QtPyVCP;
- virtual control panels (VCPs) themselves, which are works based on
  QtPyVCP;
- modules distributed as an integral part of QtPyVCP or of a VCP, or
  on which a VCP relies for its essential or primary functionality;
- any work that incorporates or adapts QtPyVCP source code.

## VCPs based on QtPyVCP

A VCP based on QtPyVCP remains subject to the GNU General Public
License.  The author of such a VCP may, for their own copyrighted
contributions, extend this exception to their VCP so that qualifying
free-standing modules may integrate with it on the same terms, but is
not obligated to do so.

## Third-party components

This exception grants no rights with respect to software that QtPyVCP
depends on but that is licensed separately by third parties, including
but not limited to PyQt (GPL or Riverbank commercial license), Qt for
Python / PySide (LGPL), and the LinuxCNC libraries and Python bindings
(GPL).  You are responsible for complying with the licenses of those
components independently of this exception.

## Scope

This exception applies only to qualifying free-standing modules.  It
does not alter the license of QtPyVCP itself: any copy of QtPyVCP,
modified or unmodified, that you distribute -- including a copy
distributed alongside a qualifying free-standing module -- remains
subject to the GNU General Public License.

If you modify QtPyVCP, you may extend this exception to your version
of QtPyVCP, but you are not obligated to do so.  If you do not wish to
do so, delete this exception statement from your version.
