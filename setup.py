import os
import versioneer
from setuptools import setup, find_packages

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
        ('/usr/share/doc/linuxcnc/examples/sample-configs/sim/qtpyvcp', 'sim'),
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
        ('~/linuxcnc/nc_files/.qtpyvcp', ['sim/example_gcode/qtpyvcp.ngc'])
    ]

    # list of (destination, source_dir) tuples
    DATA_DIRS = [
        ('~/linuxcnc/configs/sim.qtpyvcp', 'sim'),
        # ('~/linuxcnc/vcps', 'examples'),
    ]


def data_files_from_dirs(data_dirs):
    data_files = []
    for dest_dir, source_dir in data_dirs:
        dest_dir = os.path.expanduser(dest_dir)
        for root, dirs, files in os.walk(source_dir):
            root_files = [os.path.join(root, i) for i in files]
            dest = os.path.join(dest_dir, os.path.relpath(root, source_dir))
            data_files.append((dest, root_files))

    return data_files


data_files = [(os.path.expanduser(dest), src_list) for dest, src_list in DATA_FILES]
data_files.extend(data_files_from_dirs(DATA_DIRS))

setup(
    name="qtpyvcp",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
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
    ],
    entry_points={
        'console_scripts': [
            'qtpyvcp=qtpyvcp:main',
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
        ],
        'qtpyvcp.test_vcp': [
            'vtk_test=video_tests.vtk_test',
            'opengl_test=video_tests.opengl_test',
            'qtpyvcp_test=video_tests.qtpyvcp_test',
        ],
    },
)
