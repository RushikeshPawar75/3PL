from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in third_party_logistics/__init__.py
from third_party_logistics import __version__ as version

setup(
	name="third_party_logistics",
	version=version,
	description="3pl",
	author="Dexciss Technology Pvt Ltd",
	author_email="demo@dexciss.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
