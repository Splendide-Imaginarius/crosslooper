#!/usr/bin/env python

from setuptools import setup
import os
import ast
import re

here = os.path.abspath(os.path.dirname(__file__))
os.chdir(here)

_version_re = re.compile(r'__version__\s*=\s*(.*)')
with open(os.path.join(here, 'crosslooper.py'), 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name="crosslooper",
    version=version,
    description="Calculate loop metadata on audio files.",
    author="Splendide Imaginarius",
    url="https://github.com/Splendide-Imaginarius/crosslooper",
    py_modules=["crosslooper","crosslooperdir"],
    install_requires=['numpy','scipy','matplotlib','mutagen','tqdm'],
    setup_requires=['stpl','restview'],
    python_requires='>=3.6',
    keywords='media audio file synchronization looping metadata rpg maker',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Environment :: Console',
        'Topic :: Utilities',
        'Topic :: Multimedia',
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Sound/Audio'
    ],
    entry_points="""
       [console_scripts]
       crosslooper=crosslooper:main
       crosslooperdir=crosslooperdir:main
       """
)
