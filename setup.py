import os
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

from qtpyvcp.tools.qcompile import compile
compile(['examples/probe_basic',])

data_dirs = [
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

setup(
    name="qtpyvcp",
    version="0.0.1",
    author="Kurt Jacobson",
    author_email="kcjengr@gmail.com",
    description="Qt and Python based Virtual Control Panel framework for LinuxCNC.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/Hazzy/qtpyvcp",
    download_url="https://gitlab.com/Hazzy/qtpyvcp/-/archive/master/qtpyvcp-master.tar.gz",
    packages=find_packages(),
    data_files=data_files_from_dirs(data_dirs),
    include_package_data=True,
    install_requires=[
    'docopt',
    'qtpy',
    'pyudev',
    'psutil',
    ],
    entry_points={
        'console_scripts': [
            'qtpyvcp=qtpyvcp.__main__',
            'qcompile=qtpyvcp.tools.qcompile:main',
            'mini=examples.mini.__main__',
            'brender=examples.brender.__main__',
            'probebasic=examples.probe_basic.__main__'
        ],
        'qtpyvcp.example_vcp': [
            'mini=examples.mini.mini:MiniVCP',
            'brender=examples.brender.brender:MainWindow',
            'probebasic=examples.probe_basic.probe_basic:ProbeBasic'
        ],
    },
)
