import os
from setuptools import setup, find_packages

setup(
    name = "deltares_cosmos",
    version = "0.0.10",
    author = "Maarten van Ormondt",
    author_email = "maarten.vanormondt@deltares.nl",
    description = ("Deltares CoSMoS package"),
    license = "MIT",
    keywords = "cosmos",
    url = "https://pypi.org/project/deltares-cosmos/",
    packages=find_packages(),
    package_dir={'': 'src'},
    long_description='none'
)
