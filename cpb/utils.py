# This python module provides utility functions for the cpb commands

import os

def sanitizeFilePath(config, filePathKey, pathPrefix) :
  if config[filePathKey][0] == "~" :
    config[filePathKey] = os.path.abspath(
        os.path.expanduser(config[filePathKey]))

  if config[filePathKey][0] != "/" :
    if pathPrefix is not None :
      config[filePathKey] = os.path.join(pathPrefix, config[filePathKey])
    config[filePathKey] = os.path.abspath(config[filePathKey])
