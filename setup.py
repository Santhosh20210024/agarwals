from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in agarwals/__init__.py
from agarwals import __version__ as version

setup(
	name="agarwals",
	version=version,
	description="Agarwals",
	author="Agarwals",
	author_email="tfs-agarwals@techfinite.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
