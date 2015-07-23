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

long_description = read_file('README.rst').strip().split('split here', 1)[0]
version = __import__('tbk').__version__

setup(
    name='tbk',
    version=version,
    description=__import__('tbk').__doc__.strip(),
    long_description=long_description,
    author='Pedro Buron',
    author_email='pedroburonv@gmail.com',
    maintainer='Pedro Buron',
    maintainer_email='pedroburonv@gmail.com',
    url='http://github.com/pedroburon/tbk',
    download_url='http://github.com/pedroburon/tbk/archive/{version}.zip'.format(version=version),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Environment :: Console',
        'Environment :: Web Environment',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    keywords=['webpay', 'chile', 'payments', 'transbank', 'kcc'],
    install_requires=[
        'requests>=2.3.0',
        'six>=1.7.3',
        'PyCrypto>=2.6.1',
        'pytz',
    ],
    tests_require=[
        'mock>=1.0.1',
        'nose>=1.3.3',
    ],
    packages=find_packages(),
    test_suite='nose.collector',
    zip_safe=True,
    license='GPLv3'
)
