#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = ["Click>=6.0", "PyGObject==3.30.4"]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author="Lizet Gomez",
    author_email="algomezb@unal.edu.co",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Students",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Una máquina virtual para el lenguaje CH.",
    entry_points={"console_scripts": ["chmaquina=chmaquina.cli:main"]},
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords="ch-maquina",
    name="py-chmaquina",
    packages=find_packages(include=["sc2reaper"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/miguelgondu/sc2reaper",
    version="0.1.0",
    zip_safe=False,
)
