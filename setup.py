from setuptools import setup, find_packages

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
    install_requires=[
    'docopt',
    ],
    entry_points={
        'console_scripts': [
            'qtpyvcp=main',
            'mini=examples.mini.mini:main',
            'brender=examples.brender.main:main'
        ],
        'qtpyvcp.example_vcp': [
            'mini=examples.mini.mini:MiniVCP',
            'brender=examples.brender.brender:MainWindow'
        ],
    },
)
