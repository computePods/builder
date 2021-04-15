# This python3 click subcommand creates a new pde commons area

import click
import importlib.resources
import jinja2
import logging
import os
import pyzipper
import random
import stat
import string
import sys
import time
import yaml

from cpb.utils import *

defaultCekitImageDescriptions = {
  'defaults'          : {
    'version'         : '1.0',
    'basedOn'         : 'debian:stable-slim',
    'description'     : 'A computePod worker',
    'modules'         : [],
    'packagesManager' : 'apt-get',
    'repositories'    : []
  },
  'natServer'         : {
    'basedOn'         : 'alpine',
    'description'     : 'The NATS messaging back-plane',
    'modules'         : [ 
      'nats'
    ],
    'packagesManager' : 'apk',
  },
  'syncThingServer'   : {
    'basedOn'         : 'alpine',
    'description'     : 'The SyncThing file syncronization back-plane',
    'modules'         : [ 
      'syncThing'
    ],
    'packagesManager' : 'apk',
  }
}

############################################################################
# Configuration

def normalizeConfig(config) :

  if 'cpf' not in config :
    logging.error("A compute pod federation (cpf) descript MUST be provided!")
    sys.exit(-1)

  if 'federationName' not in config['cpf'] :
    logging.error("A compute pod federation name MUST be provided!")
    sys.exit(-1)

  config['federationName'] = config['cpf']['federationName']
  
  setDefault(      config, 'buildBaseDir', os.path.join("~", ".local", "computePods"))
  sanitizeFilePath(config, 'buildBaseDir', None)
  setDefault(      config, 'buildDir',     os.path.join(config['buildBaseDir'], config['federationName']) )  

  if 'computePods' not in config['cpf'] :
    logging.error("A compute pod federation name MUST have some computePods defined!")
    sys.exit(-1)  

  if 'cekitImageDescriptions' not in config['cpf'] :
    logging.error("A compute pod federation name MUST have some cekit image descriptions defined!")
    sys.exit(-1)  

  images = {}
  imageList = config['cpf']['podDefaults']['images']
  for anImage in imageList :
    images[anImage] = True
  computePods = config['cpf']['computePods']
  for aPod in computePods :
    if 'images' in aPod :
      for anImage in aPod['images'] :
        images[anImage] = True
  config['imagesToBuild'] = list(images.keys())

  defaultImageDesc = defaultCekitImageDescriptions['defaults']
  config['buildCekitModulesDir'] = os.path.join(config['buildDir'], 'cekitModules')
  
  imageDescs = config['cpf']['cekitImageDescriptions'] 
  if 'defaults' not in imageDescs :
    imageDescs['defaults'] = {}
  mergeCekitImageDescriptions(imageDescs['defaults'], defaultImageDesc)
  imageDescs['defaults']['repositories'].insert(0, config['buildCekitModulesDir'])
  imageDefaults = imageDescs['defaults']

  for anImageName, anImageDesc in imageDescs.items() :
    if anImageName != 'defaults' :
      mergeCekitImageDescriptions(anImageDesc, imageDefaults)
      setDefault(anImageDesc, 'name',      anImageName)
      setDefault(anImageDesc, 'imageName', "{}-{}".format(config['federationName'], anImageName))
      anImageDesc['modules'].insert(len(defaultImageDesc['modules']), 'cpChef')
  for anImageName, anImageDesc in defaultCekitImageDescriptions.items() :
    if anImageName != 'defaults' :
      mergeCekitImageDescriptions(anImageDesc, imageDefaults)
      if anImageName not in imageDescs :
        imageDescs[anImageName] = {}
        mergeCekitImageDescriptions(imageDescs[anImageName], anImageDesc)
      setDefault(imageDescs[anImageName], 'name',      anImageName)
      setDefault(imageDescs[anImageName], 'imageName', "{}-{}".format(config['federationName'], anImageName))

  if config['verbose'] :
    logging.info("configuration:\n------\n" + yaml.dump(config) + "------\n")

############################################################################
# some helper methods

def copyCekitModulesFile(config, pathList) :
  cekitModuleDir = os.path.join(config['buildCekitModulesDir'], pathList[0])
  os.makedirs(cekitModuleDir, exist_ok=True)
  fileContents = importlib.resources.read_text(
    "cpb.cekitModules.{}".format(pathList[0]),
    pathList[1]
  )
  with open(os.path.join(cekitModuleDir, pathList[1]), 'w') as outFile :
    outFile.write(fileContents)

############################################################################
# Do the work...

@click.command("build")
@click.pass_context
def build(ctx):
  """
  uses CEKit to build podman images used by this computePod.

  """
  config = ctx.obj
  normalizeConfig(config)

  copyCekitModulesFile(config, ['cpChef-apk',      'Readme.md'])
  copyCekitModulesFile(config, ['cpChef-apk',      'module.yaml'])
  copyCekitModulesFile(config, ['cpChef-apk',      'installCPChef.sh'])
  copyCekitModulesFile(config, ['cpChef-apt-get',  'Readme.md'])
  copyCekitModulesFile(config, ['cpChef-apt-get',  'module.yaml'])
  copyCekitModulesFile(config, ['cpChef-apt-get',  'installCPChef.sh'])
  copyCekitModulesFile(config, ['natServer',       'Readme.md'])
  copyCekitModulesFile(config, ['natServer',       'module.yaml'])
  copyCekitModulesFile(config, ['natServer',       'installNats.sh'])
  copyCekitModulesFile(config, ['syncThingServer', 'Readme.md'])
  copyCekitModulesFile(config, ['syncThingServer', 'module.yaml'])
  copyCekitModulesFile(config, ['syncThingServer', 'installSyncThing.sh'])

  imageDescs = config['cpf']['cekitImageDescriptions']
  for anImageKey in config['imagesToBuild'] :

    if anImageKey not in imageDescs :
      logging.error("No cekit image description provided for the {} image!".format(anImageKey))
      sys.exit(-1)

    imageDir = os.path.join(config['buildDir'], anImageKey)
    fileName = 'image.yaml'
    os.makedirs(imageDir, exist_ok=True)
    cekitImageJ2 = importlib.resources.read_text('cpb.templates', 'cekitImage.yaml.j2')
    try: 
      template = jinja2.Template(cekitImageJ2)
      fileContents = template.render(imageDescs[anImageKey]) 
      with open(os.path.join(imageDir, "image.yaml"), 'w') as outFile :
        outFile.write(fileContents)
    except Exception as err:
      logging.error("Could not render the Jinja2 template [{}]".format(fileName))
      logging.error(err)

    try:
      os.chdir(imageDir)
      click.echo("----------------------------------------------------------")
      click.echo("Using CEKit to build the {} image".format(anImageKey))
      click.echo("in the {} directory".format(imageDir))
      click.echo("")
      os.system("cekit build podman")
      click.echo("----------------------------------------------------------")
    except Exception as err:
      logging.error("Could not build {} image using CEKit".format(anImageKey))
      logging.error(err)

  """
  for anObj in importlib.resources.contents('cpb') :
    click.echo(anObj)
  aFileStr = importlib.resources.read_text('cpb.templates', 'sillyTemplate.j2')
  click.echo("----------------------")
  click.echo(aFileStr)
  click.echo("----------------------")
  with importlib.resources.path('cpb.templates', 'sillyTemplate.j2') as aPath :
    click.echo(aPath)
  """
