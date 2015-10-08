from setuptools import find_packages
from setuptools import setup
import os


version = '1.3.1'
shortdesc = "An alternative to mixin-based extension of classes."
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()


setup(name='plumber',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Software Development',
      ],
      keywords='',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url='http://github.com/bluedynamics/plumber',
      license='Python Software Foundation License',
      packages=find_packages('src'),
      package_dir={'': 'src'},
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
              'zope.deprecation',
          ],
      },
      entry_points="""
      """)
