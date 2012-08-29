from setuptools import setup, find_packages
import sys, os

version = '0.1'

long_description = (
    open('README.rst').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.txt').read()
    + '\n' +
    open('CHANGES.txt').read()
    + '\n')

setup(name='assentio',
      version=version,
      description="A minimal, lightweight flask-based blog",
      long_description=long_description,
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Antonio Sagliocco',
      author_email='asagliocco@gmail.com',
      url='https://github.com/kalymero/assentio',
      license='WTFPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      test_suite="assentio.tests",
      install_requires=[
          'setuptools',
          'blinker', 
          'Flask',
          'WTForms==1.0.1',
          'Flask-admin==1.0.1',
          'Flask-login',
          'Flask-sqlalchemy',
          'Flask-bcrypt',
          'Flask-DebugToolbar',
          'Flask-Script', 
      ],
      entry_points={
          'console_scripts': ['runserver = assentio.main:runserver',
                              'manage = assentio.manage:manage']
      }
      )
