# This python module provides utility functions for the cpb commands

import os

def getRegistryFlagAndPath(imageName, registry) :
  registryFlag = "--tls-verify=false"
  if 'isSecure' in registry and registry['isSecure'] :
    registryFlag = "--tls-verify=true"

  registryPath = ""
  if 'host' in registry :
    registryPath = registry['host']
  if 'port' in registry :
    registryPath += ':{}'.format(registry['port'])
  if 'path' in registry :
    if registry['path'][0] != '/' :
      registryPath += '/'
    registryPath += registry['path']
  registryPath += '/{}'.format(imageName)
  return registryFlag, registryPath.lower()

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

def prependListDefaults(eData, key, value) :
  newList = []
  if key in value :
    for aValue in value[key] :
      newList.append(aValue)
  if key in eData :
    for aValue in eData[key] :
      newList.append(aValue)
  eData[key] = newList

def appendListDefaults(eData, key, value) :
  newList = []
  if key in eData :
    for aValue in eData[key] :
      newList.append(aValue)
  if key in value :
    for aValue in value[key] :
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
  appendListDefaults(eData, 'hosts',         podDefaults)
  mergeDictDefaults( eData, 'ports',         podDefaults)
  appendListDefaults(eData, 'volumes',       podDefaults)
  mergeDictDefaults( eData, 'envs',          podDefaults)
  appendListDefaults(eData, 'secrets',       podDefaults)
  setDefault(        eData, 'maxLoadPerCPU', podDefaults['maxLoadPerCPU'])
  appendListDefaults(eData, 'images',        podDefaults)
  appendListDefaults(eData, 'baseImages',    podDefaults)

def mergeCekitImageDescriptions(iData, imageDefaults) :
  setDefault(      iData, 'curDir', os.path.abspath(os.getcwd()))
  sanitizeFilePath(iData, 'curDir', None)

  setDefault(         iData, 'basedOn',         imageDefaults['basedOn'])
  setDefault(         iData, 'buildBasedOn',    imageDefaults['buildBasedOn'])
  setDefault(         iData, 'description',     imageDefaults['description'])
  setDefault(         iData, 'version',         imageDefaults['version'])
  setDefault(         iData, 'packagesManager', imageDefaults['packagesManager'])
  prependListDefaults(iData, 'modules',         imageDefaults)
  prependListDefaults(iData, 'repositories',    imageDefaults)
  newRepos = []
  for aRepo in iData['repositories'] :
    tmpDict = { 'repo' : aRepo }
    sanitizeFilePath(tmpDict, 'repo', iData['curDir'])
    newRepos.append(tmpDict['repo'])
  iData['repositories'] = newRepos
