import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'pyramid',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'SQLAlchemy',
    'transaction',
    'alembic',
    'rhombus',
    'whoosh',
    'pandas',
    'docutils',
    'pyramid_rpc',
    'joblib',
    'more_itertools',
    'simplejson',
    'pyparsing',
]

setup(name='MESSy',
      version='0.0',
      description='MESSy',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='messy',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = messy:main
      [console_scripts]
      messy-run = messy.scripts.run:main
      messy-shell = messy.scripts.shell:main
      """,
      )

# EOF
