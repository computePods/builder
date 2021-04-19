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
      'natServer'
    ],
    'packagesManager' : 'apk',
  },
  'syncThingServer'   : {
    'basedOn'         : 'alpine',
    'description'     : 'The SyncThing file syncronization back-plane',
    'modules'         : [ 
      'syncThingServer'
    ],
    'packagesManager' : 'apk',
  }
}

############################################################################
# some helper methods

def copyCekitModulesFiles(config) :
  for aCekitModule in importlib.resources.contents("cpb.cekitModules") :
    if aCekitModule == '__init__.py' : continue
    if aCekitModule == '__pycache__' : continue
    cekitModuleDir = os.path.join(config['buildCekitModulesDir'], aCekitModule)
    os.makedirs(cekitModuleDir, exist_ok=True)
    for aFile in importlib.resources.contents("cpb.cekitModules.{}".format(aCekitModule)) :
      if aFile == '__init__.py' : continue
      if aFile == '__pycache__' : continue
      logging.info("copying cekit module file: {}::{}".format(aCekitModule, aFile))
      fileContents = importlib.resources.read_text(
        "cpb.cekitModules.{}".format(aCekitModule), aFile )
      with open(os.path.join(cekitModuleDir, aFile), 'w') as outFile :
        outFile.write(fileContents)

############################################################################
# Configuration

def loadCekitModules(config) :
  config['modules'] = {}
  modules = config['modules']
  
  for aRepo in config['repositories'] :
    for aModule in os.listdir(aRepo) :
      modules[aModule] = {}
      
      cekitModulePath = os.path.join(aRepo, aModule, 'module.yaml')
      if os.path.isfile(cekitModulePath) :
        try: 
          with open(cekitModulePath, 'r') as moduleFile :
            logging.info("Loading {}::module.yaml\n      from {}".format(aModule, aRepo))
            modules[aModule] = yaml.safe_load(moduleFile)
        except Exception as e :
          logging.info("Could not load the {} YAML file.".format(cekitModulePath))
          print("  > " + "\n  >".join(str(e).split("\n")))
          
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
  setDefault(      config, 'cekitCmd',     os.path.join(config['buildDir'], 'cpb-cekit'))

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

  copyCekitModulesFiles(config)
  
  config['repositories'] = []
  for aRepo in imageDescs['defaults']['repositories'] :
    config['repositories'].append(aRepo)
  loadCekitModules(config)

  # Process the user's image definitions
  #
  for anImageName, anImageDesc in imageDescs.items() :
    if anImageName != 'defaults' :
      mergeCekitImageDescriptions(anImageDesc, imageDefaults)
      setDefault(anImageDesc, 'name',      anImageName)
      setDefault(anImageDesc, 'imageName', "{}-{}".format(config['federationName'], anImageName))
      anImageDesc['modules'].insert(len(defaultImageDesc['modules']), 'cpChef-{}'.format(anImageDesc['packagesManager']))
  #
  # Add in the default image definitions (defined above)
  #
  for anImageName, anImageDesc in defaultCekitImageDescriptions.items() :
    if anImageName != 'defaults' :
      mergeCekitImageDescriptions(anImageDesc, imageDefaults)
      if anImageName not in imageDescs :
        imageDescs[anImageName] = {}
        mergeCekitImageDescriptions(imageDescs[anImageName], anImageDesc)
      setDefault(imageDescs[anImageName], 'name',      anImageName)
      setDefault(imageDescs[anImageName], 'imageName', "{}-{}".format(config['federationName'], anImageName))
  #
  # Now add any required build modules
  #
  modules = config['modules']
  for anImageName, anImageDesc in imageDescs.items() :
    if anImageName != 'defaults' :
      buildModules = []

      for aModule in anImageDesc['modules'] :
        if aModule not in modules :
          logging.error("No {} module found while defining the {} image".format(aModule, anImageName))
          sys.exit(-1)
        
        if 'buildModule' in modules[aModule] :
          buildModules.append(modules[aModule]['buildModule'])
      if buildModules :
        anImageDesc['buildModules'] = buildModules
      
  if config['verbose'] :
    logging.info("configuration:\n------\n" + yaml.dump(config) + "------\n")

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

  cekitMonkeyPatch = importlib.resources.read_text(
    "cpb.resources", "cekitWithExtendedModule" )
  with open(config['cekitCmd'], 'w') as outFile :
    outFile.write(cekitMonkeyPatch)
  os.chmod(config['cekitCmd'], 
    stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | 
    stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
    stat.S_IROTH | stat.S_IXOTH)

  imageDescs = config['cpf']['cekitImageDescriptions']
  for anImageKey in config['imagesToBuild'] :

    if anImageKey not in imageDescs :
      logging.error("No cekit image description provided for the {} image!".format(anImageKey))
      sys.exit(-1)

    imageDir = os.path.join(config['buildDir'], anImageKey)
    fileName = 'image.yaml'
    os.makedirs(imageDir, exist_ok=True)
    cekitImageJ2 = importlib.resources.read_text('cpb.resources', 'cekitImage.yaml.j2')
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
      os.system("echo cekit build podman")
      click.echo("----------------------------------------------------------")
    except Exception as err:
      logging.error("Could not build {} image using CEKit".format(anImageKey))
      logging.error(err)
