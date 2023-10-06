from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in tacten_vending_machine/__init__.py
from tacten_vending_machine import __version__ as version

setup(
	name="tacten_vending_machine",
	version=version,
	description="Manufactures Vending Machines and deploy it to customer sites",
	author="Aerele Technologies",
	author_email="hello@aerele.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
