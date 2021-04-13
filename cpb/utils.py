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

def setDefault(eData, key, value) :
  if key not in eData :
    eData[key] = value

def appendListDefaults(eData, key, value) :
  newList = []
  if key in value :
    for aValue in value[key] :
      newList.append(aValue)
  if key in eData :
    for aValue in eData[key] :
      newList.append(aValue)
  eData[key] = newList

def mergeDictDefaults(eData, key, value) :
  newDict = {}
  if key in value :
    for subKey, subValue in value[key].items() :
      newDict[subKey] = subValue
  if key in eData :
    for subKey, subValue in eData[key].items() :
      newDict[subKey] = subValue
  eData[key] = newDict

def mergePodDefaults(eData, podDefaults) :
  setDefault(        eData, 'commons',       os.path.join("$HOME", "commons"))
  if 0 <= eData['commons'].find("$HOME") :
    if 'HOME' in os.environ :
      eData['commons'] = eData['commons'].replace("$HOME", os.environ['HOME'])
    else: 
      eData['commons'] = eData['commons'].replace("$HOME", "")
      
  appendListDefaults(eData, 'hosts',         podDefaults)
  mergeDictDefaults( eData, 'ports',         podDefaults)
  appendListDefaults(eData, 'volumes',       podDefaults)
  mergeDictDefaults( eData, 'envs',          podDefaults)
  appendListDefaults(eData, 'secrets',       podDefaults)
  setDefault(        eData, 'maxLoadPerCPU', podDefaults['maxLoadPerCPU'])
  appendListDefaults(eData, 'images',        podDefaults)
