import os
import platform
import sys

import versioneer
from setuptools import setup, find_packages, Extension
from multiprocessing import cpu_count

with open("README.md", "r") as fh:
    long_description = fh.read()


if os.getenv('DEB_BUILD') == 'true' or os.getenv('USER') == 'root':
    "/usr/share/doc/linuxcnc/examples/sample-configs/sim"
    # list of (destination, source_file) tuples
    DATA_FILES = [
        ('/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/', [
            'pyqt5designer/Qt5.7.1-64bit/libpyqt5_py2.so',
            'pyqt5designer/Qt5.7.1-64bit/libpyqt5_py3.so']),
    ]

    # list of (destination, source_dir) tuples
    DATA_DIRS = [
        ('/usr/share/doc/linuxcnc/examples/sample-configs/sim', 'linuxcnc/configs'),
    ]

    if os.getenv('USER') == 'root':
        try:
            os.rename('/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/libpyqt5.so',
                      '/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/libpyqt5.so.old')
        except:
            pass

else:
    # list of (destination, source_file) tuples
    DATA_FILES = [
        ('~/', ['scripts/.xsessionrc',]),
    ]

    # list of (destination, source_dir) tuples
    DATA_DIRS = [
        ('utilities/vcp_chooser', 'qtpyvcp/utilities/vcp_chooser/vcp_chooser.ui'),
        ('~/linuxcnc/configs/sim.qtpyvcp', 'linuxcnc/configs/sim.qtpyvcp'),
        ('~/linuxcnc/nc_files/qtpyvcp', 'linuxcnc/nc_files/qtpyvcp'),

        # ('~/linuxcnc/vcps', 'examples'),
    ]

CYTHON = platform.python_implementation() != "PyPi"

if CYTHON is True:
    from setuptools import dist
    dist.Distribution().fetch_build_eggs(["cython>=0.29.16"])

    from Cython.Build import cythonize
    import Cython.Compiler.Options
    from Cython.Distutils import build_ext


def data_files_from_dirs(data_dirs):
    data_files = []
    for dest_dir, source_dir in data_dirs:
        dest_dir = os.path.expanduser(dest_dir)
        for root, dirs, files in os.walk(source_dir):
            root_files = [os.path.join(root, i) for i in files]
            dest = os.path.join(dest_dir, os.path.relpath(root, source_dir))
            data_files.append((dest, root_files))

    return data_files


ROOT_DIR = "qtpyvcp"


# Define libs, libdirs, includes and cflags for SDL2
def define_lib_includes_cflags():
    libs = []
    libdirs = []
    includes = []
    cflags = []

    return libs, libdirs, includes, cflags


def prep_pxd_py_files():
    ignore_py_files = ["__main__.py", "glcanon.py"]
    # Cython doesn't trigger a recompile on .py files, where only the .pxd file has changed. So we fix this here.
    # We also yield the py_files that have a .pxd file, as we feed these into the cythonize call.
    for root, dirs, files in os.walk(ROOT_DIR):
        for f in files:
            if os.path.splitext(f)[1] == ".py" and f not in ignore_py_files:
                yield os.path.join(root, f)
            if os.path.splitext(f)[1] == ".pxd":
                py_file = os.path.join(root, os.path.splitext(f)[0]) + ".py"
                if os.path.isfile(py_file):
                    if os.path.getmtime(os.path.join(root, f)) > os.path.getmtime(py_file):
                        os.utime(py_file)


# Cython seems to cythonize these before cleaning, so we only add them, if we aren't cleaning.
ext_modules = None
if CYTHON and "clean" not in sys.argv:
    if sys.platform == "win32":
        # Cython currently has a bug in its code that results in symbol collision on Windows
        def get_export_symbols(self, ext):
            parts = ext.name.split(".")
            initfunc_name = "PyInit_" + parts[-2] if parts[-1] == "init" else parts[-1] # noqa: F841

        # Override function in Cython to fix symbol collision
        build_ext.get_export_symbols = get_export_symbols
        thread_count = 0 # Disables multiprocessing (windows)
    elif platform.python_version().startswith("3.8"):
        # Causes infinite recursion
        thread_count = 0
    else:
        thread_count = cpu_count()

    # Set up some values for use in setup()
    libs, libdirs, includes, cflags = define_lib_includes_cflags()

    py_pxd_files = prep_pxd_py_files()
    cythonize_files = map(
        lambda src: Extension(
            src.split(".")[0].replace(os.sep, "."), [src],
            include_dirs=includes,
            library_dirs=libdirs,
            libraries=libs,
            extra_compile_args=cflags
        ), list(py_pxd_files)
    )
    c_files = list()
    for c_file in cythonize_files:
        c_files.append(c_file)

    ext_modules = cythonize(
        c_files,  # This runs even if build_ext isn't invoked...
        nthreads=thread_count,
        annotate=False,
        gdb_debug=False,
        language_level=2,
        compiler_directives={
            "boundscheck": False,
            "cdivision": True,
            "cdivision_warnings": False,
            "infer_types": True,
            "initializedcheck": False,
            "nonecheck": False,
            "overflowcheck": False,
            # "profile" : True,
            "wraparound": False,
        },
    )

try:
    this_directory = os.path.abspath(os.path.dirname(file))
    with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except Exception as e:
    print("README.md not found")
    long_description = ""


data_files = [(os.path.expanduser(dest), src_list) for dest, src_list in DATA_FILES]
data_files.extend(data_files_from_dirs(DATA_DIRS))


# Define libs, libdirs, includes and cflags for SDL2
def define_lib_includes_cflags():
    libs = []
    libdirs = []
    includes = []
    cflags = []

    return libs, libdirs, includes, cflags


def prep_pxd_py_files():
    ignore_py_files = ["__main__.py", "glcanon.py"]
    # Cython doesn't trigger a recompile on .py files, where only the .pxd file has changed. So we fix this here.
    # We also yield the py_files that have a .pxd file, as we feed these into the cythonize call.
    for root, dirs, files in os.walk(ROOT_DIR):
        for f in files:
            if os.path.splitext(f)[1] == ".py" and f not in ignore_py_files:
                yield os.path.join(root, f)
            if os.path.splitext(f)[1] == ".pxd":
                py_file = os.path.join(root, os.path.splitext(f)[0]) + ".py"
                if os.path.isfile(py_file):
                    if os.path.getmtime(os.path.join(root, f)) > os.path.getmtime(py_file):
                        os.utime(py_file)


# Cython seems to cythonize these before cleaning, so we only add them, if we aren't cleaning.
ext_modules = None
if CYTHON and "clean" not in sys.argv:

    if platform.python_version().startswith("3.8"):
        # Causes infinite recursion
        thread_count = 0
    else:
        thread_count = cpu_count()

    # Set up some values for use in setup()
    libs, libdirs, includes, cflags = define_lib_includes_cflags()

    py_pxd_files = prep_pxd_py_files()
    cythonize_files = map(
        lambda src: Extension(
            src.split(".")[0].replace(os.sep, "."), [src],
            include_dirs=includes,
            library_dirs=libdirs,
            libraries=libs,
            extra_compile_args=cflags
        ), list(py_pxd_files)
    )

    c_files = list()
    for c_file in cythonize_files:
        c_files.append(c_file)

    ext_modules = cythonize(
        c_files,  # This runs even if build_ext isn't invoked...
        nthreads=thread_count,
        annotate=False,
        gdb_debug=False,
        language_level=2,
        compiler_directives={
            "boundscheck": False,
            "cdivision": True,
            "cdivision_warnings": False,
            "infer_types": True,
            "initializedcheck": False,
            "nonecheck": False,
            "overflowcheck": False,
            # "profile" : True,
            "wraparound": False,
        },
    )

# data_files = [(os.path.expanduser(dest), src_list) for dest, src_list in DATA_FILES]
# data_files.extend(data_files_from_dirs(DATA_DIRS))

data_files = [('qtpyvcp/utilities/vcp_chooser', ['qtpyvcp/utilities/vcp_chooser/vcpchooser.ui'])]

setup(
    name="qtpyvcp",
    version=versioneer.get_version(),
    # cmdclass=versioneer.get_cmdclass(),
    author="Kurt Jacobson",
    author_email="kcjengr@gmail.com",
    description="Qt and Python based Virtual Control Panel framework for LinuxCNC.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GNU General Public License v2 (GPLv2)",
    url="https://github.com/kcjengr/qtpyvcp",
    download_url="https://github.com/kcjengr/qtpyvcp/archive/master.zip",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Manufacturing',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Software Development :: Widget Sets',
        'Topic :: Software Development :: User Interfaces',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(),
    data_files=data_files,
    include_package_data=True,
    install_requires=[
        'docopt',
        'qtpy',
        'pyudev',
        'psutil',
        'HiYaPyCo',
        'pyopengl',
        'vtk',
        'pyqtgraph',
        'oyaml',
        'simpleeval',
    ],
    entry_points={
        'console_scripts': [
            'qtpyvcp=qtpyvcp.app:main',
            'qcompile=qtpyvcp.tools.qcompile:main',
            'editvcp=qtpyvcp.tools.editvcp:main',

            # example VCPs
            'mini=examples.mini:main',
            'brender=examples.brender:main',

            # test VCPs
            'vtk_test=video_tests.vtk_test:main',
            'opengl_test=video_tests.opengl_test:main',
            'qtpyvcp_test=video_tests.qtpyvcp_test:main',

        ],
        'qtpyvcp.example_vcp': [
            'mini=examples.mini',
            'brender=examples.brender',
            'actions=examples.actions',
        ],
        'qtpyvcp.test_vcp': [
            'vtk_test=video_tests.vtk_test',
            'opengl_test=video_tests.opengl_test',
            'qtpyvcp_test=video_tests.qtpyvcp_test',
        ],
    },
    cmdclass={
        "build_ext": build_ext
    },
)
