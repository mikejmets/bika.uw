from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='bika.uw',
      version=version,
      description="Bika UW",
      long_description="Bika customisations for UW",
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='http://bikalabs.com',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['bika'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'bika.lims',
          'archetypes.schemaextender',
      ],
      extras_require={
          'test': [
              'plone.app.testing',
          ]
      },
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
