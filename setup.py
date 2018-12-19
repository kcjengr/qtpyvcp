import os
import versioneer
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

from qtpyvcp.tools.qcompile import compile
compile(['examples/probe_basic',])

# list of (destination, source_file) tuples
DATA_FILES = [
    ('~/', ['scripts/.xsessionrc',])
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

    print data_files
    return data_files


data_files = [(os.path.expanduser(dest), src_list) for dest, src_list in DATA_FILES]
data_files.extend(data_files_from_dirs(DATA_DIRS))

setup(
    name="qtpyvcp",
    version=versioneer.get_version(),
    author="Kurt Jacobson",
    author_email="kcjengr@gmail.com",
    description="Qt and Python based Virtual Control Panel framework for LinuxCNC.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GNU General Public License v2 (GPLv2)",
    url="https://github.com/kcjengr/qtpyvcp",
    download_url="https://gitlab.com/Hazzy/qtpyvcp/-/archive/master/qtpyvcp-master.tar.gz",
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
        'HiYaPyCo'
    ],
    entry_points={
        'console_scripts': [
            'qtpyvcp=qtpyvcp:main',
            'mini=examples.mini:main',
            'brender=examples.brender:main',
            'probebasic=examples.probe_basic:main',
            'qcompile=qtpyvcp.tools.qcompile:main',
            'editvcp=qtpyvcp.tools.editvcp:main',
        ],
        'qtpyvcp.example_vcp': [
            'mini=examples.mini',
            'brender=examples.brender',
            'probebasic=examples.probe_basic'
        ],
    },
)
