#!/usr/bin/env python

from distutils.core import setup

version = __import__('brightkite').__version__

setup(
    name="brightkite",
    version=version,
    description="Brightkite API Library.",
    author="Jon Parise",
    author_email="jon@indelible.org",
    url="",
    py_modules = ['brightkite'],
    license = "MIT License",
    classifiers = ['Development Status :: 2 - Pre-Alpha',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Internet :: WWW/HTTP :: Dynamic Content'],
)
