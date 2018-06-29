#! /usr/bin/env python
# -*- coding: utf8 -*-

import os
import io
from setuptools import setup


def read(fname):
    return io.open(os.path.join(os.path.dirname(__file__), fname),'r',encoding='utf-8').read()

setup(
    name = "NAFFoLiAPy",
    version = "0.1.1",
    author = "Antske Fokkens and Maarten van Gompel",
    author_email = "proycon@anaproy.nl",
    description = ("Converters between two formats for linguistic annotation: FoLiA and NAF"),
    license = "GPL",
    keywords = "nlp computational_linguistics linguistics converter folia naf",
    url = "https://github.com/cltl/NAFFoLiAPy",
    packages=['naffoliapy','naffoliapy.tests'],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points = {
        'console_scripts': [
            'folia2naf = naffoliapy.folia2naf:main',
            'naf2folia = naffoliapy.naf2folia:main',
        ]
    },
    zip_safe=False,
    include_package_data=True,
    package_data = {'naffoliapy': ['../examples/100911_Northrop_Grumman_and_Airbus_parent_EADS_defeat_Boeing.naf.xml']},
    install_requires=['pynlpl >= 1.2.7', 'KafNafParserPy >= 1.88', 'lxml >= 2.2','docutils']
)
