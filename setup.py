# encoding=UTF-8
#!/usr/bin/env python
import os
from setuptools import setup, find_packages


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''

long_description = read_file('README.md').strip().split('split here', 1)[0]

setup(
    name='tbk',
    version=__import__('tbk').__version__,
    description=' '.join(__import__('tbk').__doc__.splitlines()).strip(),
    long_description=long_description,
    author='Pedro Buron',
    author_email='pedroburonv@gmail.com',
    url='http://github.com/pedroburon/tbk',
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'requests>=2.3.0',
    ],
    tests_require=[
        'mock>=1.0.1',
        'nose>=1.3.3',
    ],
    packages=find_packages(),
    test_suite='nose.collector',
    zip_safe=True
)
