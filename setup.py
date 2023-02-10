from setuptools import setup, find_packages

setup(
    name="devicegen",
    packages=find_packages(),
    version="0.6.2",
    license='GPLv3+',
    author="Pericles Philippopoulos, Felix Beaudoin",
    author_email="pericles@nanoacademic.com",
    url="https://github.com/nanoacademic/devicegen",
    description="Device generator for gated quantum devices",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Topic :: Scientific/Engineering",
    ],
)
