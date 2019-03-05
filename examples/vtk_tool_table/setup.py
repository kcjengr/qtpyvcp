from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="vtk_tool_table",
    version="0.0.1",
    author="John Doe",
    author_email="<doe.john@example.com>",
    description="vtk_tool_table - A QtPyVCP based Virtual Control Panel for LinuxCNC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/USERNAME/REPO",
    download_url="https://github.com/USERNAME/REPO/tarball/master",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'gui_scripts': [
            'vtk_tool_table=vtk_tool_table:main',
        ],
        'qtpyvcp.vcp': [
            'vtk_tool_table=vtk_tool_table',
        ],
    },
)
