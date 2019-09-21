from setuptools import setup

url = "https://github.com/JIC-CSB/dmaudit"
version = "0.8.0"
readme = open('README.rst').read()

setup(
    name="dmaudit",
    packages=["dmaudit"],
    version=version,
    description="dmaudit generates data management audit reports",
    long_description=readme,
    author="Tjelvar Olsson",
    author_email="tjelvar.olsson@jic.ac.uk",
    url=url,
    install_requires=[
        "click",
        "puremagic",
    ],
    entry_points={
        'console_scripts': ['dmaudit=dmaudit.cli:dmaudit'],
    },
    download_url="{}/tarball/{}".format(url, version),
    license="MIT"
)
