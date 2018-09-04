from distutils.dir_util import copy_tree
from setuptools import setup, find_packages

import shutil
from os import path, environ, listdir

cur_dir = path.abspath(path.dirname(__file__))

examples_src = path.join(cur_dir, 'examples')
examples_dst = path.expanduser('~/linuxcnc/vcps/examples')
copy_tree(examples_src, examples_dst)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="qtpyvcp",
    version="0.0.1",
    author="Kurt Jacobson",
    author_email="kcjengr@gmail.com",
    description="PyQt5 based Virtual Control Panel (VCP) toolkit for LinuxCNC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/Hazzy/qtpyvcp",
    download_url="https://gitlab.com/Hazzy/qtpyvcp/-/archive/master/qtpyvcp-master.tar.gz",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'qtpyvcp=vcp_launcher.main:main',
        ],
        'qtpyvcp.vcp': [
            'mini=examples.mini.mini:MiniVCP',
        ],
    },
)
