from setuptools import setup, find_packages
import os

version = '0.1dev'
shortdesc = "A plumber constructs a pipeline to objects."
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()

setup(name='plumber',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            ], # Get strings from http://www.python.org/pypi?:action=list_classifiers
      keywords='',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url='http://github.com/bluedynamics/plumber',
      license='General Public Licence',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          'setuptools',
      ],
      extras_require={
          'test': [
              'interlude',
              'plone.testing',
              'unittest2',
              'zope.interface',
          ]
      },
      entry_points="""
      """,
      )
