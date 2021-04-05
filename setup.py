
import distutils
import setuptools

confDict = setuptools.config.read_configuration("setup.cfg")

metadata = confDict['metadata']
options  = confDict['options']

distutils.core.setup(
  name         = metadata['name'],
  version      = metadata['version'],
  description  = metadata['description'],
  author       = metadata['author'],
  author_email = metadata['author_email'],
  url          = metadata['url'],
  packages     = options['packages'],
  entry_points = options['entry_points'],
  install_requires = options['install_requires']
)
