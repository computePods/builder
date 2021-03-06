# This python3 click subcommand creates the individual podman images

import click
import importlib.resources
import jinja2
import logging
import os
from pathlib import Path
import random
import stat
import string
import subprocess
import sys
import time
import yaml

from cpb.utils import *

defaultCekitImageDescriptions = {
  'defaults'          : {
    'version'         : '1.0',
    'basedOn'         : 'python:slim',
    'buildBasedOn'    : 'python:slim',
    'description'     : 'A computePod worker',
    'modules'         : [],
    'packagesManager' : 'apt-get',
    'repositories'    : [],
  },
  'majorDomoServer'   : {
    'basedOn'         : 'python:alpine',
    'buildBasedOn'    : 'python:alpine',
    'description'     : 'The ComputePods MajorDomo coordination service',
    'modules'         : [
      'cpMajorDomoServer'
    ],
    'packagesManager' : 'apk',
  },
  'natsServer'         : {
    'version'         : '1.0',
    'basedOn'         : 'alpine',
    'buildBasedOn'    : 'alpine',
    'description'     : 'The NATS messaging back-plane',
    'modules'         : [
      'natsServer'
    ],
    'packagesManager' : 'apk',
  },
  'cpPyNatsFastAPI-apk' : {
    'version'         : '1.0',
    'basedOn'         : 'python:alpine',
    'buildBasedOn'    : 'python:alpine',
    'packagesManager' : 'apk',
    'description'     : 'An Alpine module which installs Python asyncio-Nats, and FastAPI',
    'modules'         : []
  },
  'cpChef-apk' : {
    'version'         : '1.0',
    'basedOn'         : 'python:alpine',
    'buildBasedOn'    : 'python:alpine',
    'packagesManager' : 'apk',
    'description'     : 'An Alpine module which installs ComputePods cpChef',
    'modules'         : [
      'cpChef-apk'
    ]
  },
  'cpPyNatsFastAPI-apt-get' : {
    'version'         : '1.0',
    'basedOn'         : 'python:slim',
    'buildBasedOn'    : 'python:slim',
    'packagesManager' : 'apt-get',
    'description'     : 'A Debian module which installs Python asyncio-Nats, and FastAPI',
    'modules'         : []
  },
  'cpChef-apt-get' : {
    'version'         : '1.0',
    'basedOn'         : 'python:slim',
    'buildBasedOn'    : 'python:slim',
    'packagesManager' : 'apt-get',
    'description'     : 'A Debian module which installs ComputePods cpChef',
    'modules'         : [
      'cpChef-apt-get'
    ]
  }
}

############################################################################
# some helper methods

def copyCekitModulesFiles(config) :
  #
  # Load the version information
  #
  versionsYAML = importlib.resources.read_text(
    "cpb.cekitModules", "versions.yaml"
  )
  versionValues = yaml.safe_load(versionsYAML)
  #
  # Now walk through each cekitModule, render any possible version
  # information and copy the resulting resources
  #
  for aCekitModule in importlib.resources.contents("cpb.cekitModules") :
    if aCekitModule == '__init__.py'   : continue
    if aCekitModule == '__pycache__'   : continue
    if aCekitModule == 'versions.yaml' : continue
    cekitModuleDir = os.path.join(config['buildCekitModulesDir'], aCekitModule)
    os.makedirs(cekitModuleDir, exist_ok=True)
    for aFile in importlib.resources.contents("cpb.cekitModules.{}".format(aCekitModule)) :
      if aFile == '__init__.py' : continue
      if aFile == '__pycache__' : continue
      logging.info("copying cekit module file: {}::{}".format(aCekitModule, aFile))
      fileContents = importlib.resources.read_text(
        "cpb.cekitModules.{}".format(aCekitModule), aFile )
      fileTemplate = jinja2.Template(fileContents)
      fileContents = fileTemplate.render(versions=versionValues)
      if aFile.endswith('.yaml') :
        fileYaml = yaml.safe_load(fileContents)
        #
        # Remove our super-set of the module.yaml format so that
        # the standard Cekit will not have problems...
        #
        if 'buildModule'    in fileYaml : del fileYaml['buildModule']
        if 'artifactImages' in fileYaml : del fileYaml['artifactImages']
        fileContents = yaml.dump(fileYaml)
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
  setDefault(      config, 'cekitCmd',     'cekit')

  if 'computePods' not in config['cpf'] :
    logging.error("A compute pod federation name MUST have some computePods defined!")
    sys.exit(-1)

  if 'cekitImageDescriptions' not in config['cpf'] :
    logging.error("A compute pod federation name MUST have some cekit image descriptions defined!")
    sys.exit(-1)

  baseImages = {}
  baseImageList = config['cpf']['podDefaults']['baseImages']
  for anImage in baseImageList :
    baseImages[anImage] = True
  computePods = config['cpf']['computePods']
  for aPod in computePods :
    if 'baseImages' in aPod :
      for anImage in aPod['baseImages'] :
        baseImages[anImage] = True

  images = {}
  podImageList = config['cpf']['podDefaults']['images']
  for anImage in podImageList :
    images[anImage] = True
  natsImageList = config['cpf']['natsDefaults']['images']
  for anImage in natsImageList :
    images[anImage] = True
  majorDomoImageList = config['cpf']['majorDomoDefaults']['images']
  for anImage in majorDomoImageList :
    images[anImage] = True
  computePods = config['cpf']['computePods']
  for aPod in computePods :
    if 'images' in aPod :
      for anImage in aPod['images'] :
        images[anImage] = True

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
      #anImageDesc['modules'].insert(len(defaultImageDesc['modules']), 'cpChef-{}'.format(anImageDesc['packagesManager']))
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
  # Correct the image names of any baseImages
  #
  for anImageName in baseImages.keys() :
    imageDescs[anImageName]['imageName'] = imageDescs[anImageName]['name']
  #
  # Now add any required build modules
  #
  #print("--------------------------------------------------------------")
  #print(yaml.dump(config))
  #print("--------------------------------------------------------------")
  modules = config['modules']
  for anImageName, anImageDesc in imageDescs.items() :
    if anImageName != 'defaults' :
      buildModules = []
      artifactImages = {}

      for aModule in anImageDesc['modules'] :
        if aModule not in modules :
          logging.error("No {} module found while defining the {} image".format(aModule, anImageName))
          sys.exit(-1)

        if 'buildModule' in modules[aModule] :
          buildModules.append(modules[aModule]['buildModule'])
        if 'artifactImages' in modules[aModule] :
          for anArtifactImage in modules[aModule]['artifactImages'] :
            artifactImages[anArtifactImage] = True
      if buildModules :
        anImageDesc['buildModules'] = buildModules
      if artifactImages :
        anImageDesc['artifactImages'] = list(artifactImages.keys())

  config['baseImagesToBuild'] = list(baseImages.keys())
  config['imagesToBuild'] = list(images.keys())

  if config['verbose'] :
    logging.info("configuration:\n------\n" + yaml.dump(config) + "------\n")

############################################################################
# Do the work...

def pushToRegistry(imageName, registry) :
    registryFlag, registryPath = getRegistryFlagAndPath(imageName, registry)
    try:
      cmd = "podman push {} {} docker://{}".format(registryFlag, imageName.lower(), registryPath)
      logging.info("pushing image using:\n  {}".format(cmd))
      os.system(cmd)
    except Exception as err :
      logging.error("Could not push the {} image to the {} registry.".format(imageName, registryPath))
      logging.error("Do you need to login to the registry using podman?")
      logging.error(err)

def buildAnImage(anImageKey, imageDescs, config, overwrite, push) :
  if anImageKey not in imageDescs :
    click.echo("No cekit image description provided for the {} image!".format(anImageKey))
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
    click.echo("Could not render the Jinja2 template [{}]".format(fileName))
    click.echo(err)

  imageName = imageDescs[anImageKey]['imageName']
  imageNameLower = imageName.lower()
  imageVersion = imageDescs[anImageKey]['version']
  click.echo("\nChecking if the {} image exists".format(imageName))
  if ((os.system("podman image exists {}".format(imageNameLower)) == 0) or
    (os.system("podman image exists {}:{}".format(imageNameLower, imageVersion)) == 0)) :
    if push and 'registry' in config['cpf'] :
      pushToRegistry(imageName, config['cpf']['registry'])
      return
    else:
      if not overwrite :
        click.echo("The {} image already exists and won't be overwritten.".format(imageName))
        click.echo("  use the --overwrite option to overwrite this image.")
        return
      else:
        click.echo("Removing the {} image".format(imageName))
        os.system("podman image rm {}".format(imageNameLower))
        time.sleep(1)
        click.echo("Removing the {}:{} image".format(imageName, imageVersion))
        os.system("podman image rm {}:{}".format(imageNameLower, imageVersion))

  try:
    os.chdir(imageDir)
    click.echo("----------------------------------------------------------")
    click.echo("Using CEKit to build the {} image".format(anImageKey))
    click.echo("in the {} directory".format(imageDir))
    click.echo("----------------------------------------------------------")
    os.system("cekit build podman")
    click.echo("----------------------------------------------------------")
  except Exception as err :
    logging.error("Could not build {} image using CEKit".format(anImageKey))
    logging.error(err)

  if push and 'registry' in config['cpf'] :
    pushToRegistry(imageName, config['cpf']['registry'])


@click.command("build")
@click.option("-P", "--push", default=False, is_flag=True,
  help="Push images to the federation registry.",
  prompt="Do you want to push images to the federation registry?")
@click.option("-O", "--overwrite", default=False, is_flag=True,
  help="Allow existing images to be overwritten.",
  prompt="Do you want to overwite images?")
@click.pass_context
def build(ctx, overwrite, push):
  """
  uses CEKit to build podman images used by this computePod.

  """
  config = ctx.obj
  normalizeConfig(config)

  if push and 'registry' not in config['cpf'] :
    click.echo("You have asked to push images to a registry...")
    click.echo("  ... but you have not specified a registry in the cpf.yaml")
    click.echo("  we will NOT push images!")

  imageDescs = config['cpf']['cekitImageDescriptions']

  # Prebuild step
  for aRepo in config['repositories'] :
    repoDir = Path(aRepo)
    for aPreBuildScript in repoDir.glob('**/preBuild.*') :
      if aPreBuildScript.is_file() \
        and os.access(str(aPreBuildScript), os.X_OK) :
        print(f"\nPreBuilding using the script:\n  {aPreBuildScript}")
        print(f"in the directory:\n  {aPreBuildScript.parent}")
        print("--------------------------------------------------------")
        subprocess.run(aPreBuildScript, cwd=aPreBuildScript.parent)
        print("--------------------------------------------------------")
      else :
        print(f"The PreBuild script:\n  {aPreBuildScript}\nis NOT executable")

  # Start by building any base images we know about
  for anImageKey in config['baseImagesToBuild'] :
    buildAnImage(anImageKey, imageDescs, config, overwrite, push)

  # Now build the container images
  for anImageKey in config['imagesToBuild'] :
    buildAnImage(anImageKey, imageDescs, config, overwrite, push)

def listSubModules(indent, aModule, modules) :
  print("{}- {}".format(indent, aModule))
  if aModule in modules :
    if 'modules' in modules[aModule] :
      if modules[aModule]['modules'] :
        if 'install' in modules[aModule]['modules'] :
          #print(yaml.dump(modules[aModule]['modules']['install']))
          for aSubModule in modules[aModule]['modules']['install'] :
            #print(yaml.dump(aSubModule))
            listSubModules(indent+"  ", aSubModule['name'], modules)

@click.command("images")
@click.pass_context
def images(ctx) :
  """
  lists the images that will be built by the build command.
  """

  config = ctx.obj
  normalizeConfig(config)

  imagesToBuild = config['imagesToBuild'] + config['baseImagesToBuild']

  imageDescs = config['cpf']['cekitImageDescriptions']
  for anImage, aDesc in imageDescs.items() :
    if anImage == 'defaults' : continue
    if anImage not in imagesToBuild : continue
    #print(anImage)
    #print(yaml.dump(aDesc))

    print("\n{}:\t{}".format(aDesc['imageName'], aDesc['description']))
    print("    basedOn: {}".format(aDesc['basedOn']))
    print("    modules:")
    for aModule in aDesc['modules'] :
      listSubModules("      ", aModule, config['modules'])
  print("")
  #print("-----------------------------------------------------")
  #print(yaml.dump(imageDescs))
