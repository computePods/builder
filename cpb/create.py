# This python3 click subcommand creates the image and cpb descriptions
# used by subsequence subcommands.

import click
import datetime
import importlib.resources
import jinja2
import logging
import os
import py7zr
import random
import stat
import string
import sys
import time
import yaml

from cpb.utils import *

# We use openssl and ssh-keygen from the command line...
#
# See: https://www.openssl.org/docs/manmaster/man5/x509v3_config.html
# see: https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl
#
# Examples:
#   https://megamorf.gitlab.io/cheat-sheets/openssl/
#   https://access.redhat.com/solutions/28965
#   https://gist.github.com/thisismitch/bf52b0c1823da27ff353
#

############################################################################
# Configuration

def generateNewPassword(passwords, eData, config) :
  passwordCharacters = string.ascii_letters + string.digits
  randomPassword =  "".join(random.choice(passwordCharacters) for x in range(config['passwordLength']))
  setDefault(passwords, eData['name'], randomPassword)
  eData['password'] = passwords[eData['name']]

def normalizeSshEntity(config, eData, workDirKey) :
  setDefault(eData, 'name', config['federationName']+'-rsync')
  timeNow = datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
  setDefault(eData, 'comment',  timeNow+'-'+eData['name'])
  eData['workDir'] = config[workDirKey]
  setDefault(eData, 'keyFile', eData['name'] + '-rsa')
  sanitizeFilePath(eData, 'keyFile', eData['workDir'])
  setDefault(eData, 'keySize', config['cpf']['keySize'])
  generateNewPassword(config['passwords']['ca'], eData, config)

def normalizeSslEntity(config, eData, eNum, workDirKey, caData, podDefaults) :
  passwords = config['passwords']['ca']
  if workDirKey == 'certificateAuthorityDir' :
    if 'federationName' not in eData :
      logging.error("All certificate authorities MUST have a 'federationName' key")
      sys.exit(-1)
    passwords = config['passwords']['ca']
    eData['name'] = eData['federationName'] + '-ca'
  if workDirKey == 'podsDir' :
    if 'host' not in eData :
      logging.error("All pods MUST have a 'host' key")
      sys.exit(-1)
    passwords = config['passwords']['pods']
    eData['name'] = eData['host'].split(',')[0]
  if workDirKey == 'usersDir' :
    if 'name' not in eData :
      logging.error("All users MUST have a 'name' key")
      sys.exit(-1)
    passwords = config['passwords']['users']

  eData['name'] = eData['name'].replace("@", "-")
  eData['workDir'] = os.path.join(config[workDirKey], eData['name'].replace(" ",""))

  setDefault(eData, 'sslConfigFile', eData['name'] + '.conf')
  sanitizeFilePath(eData, 'sslConfigFile', eData['workDir'])

  setDefault(eData, 'csrFile', eData['name'] + '-csr.conf')
  sanitizeFilePath(eData, 'csrFile', eData['workDir'])

  setDefault(eData, 'certFile', eData['name'] + '-crt.pem')
  sanitizeFilePath(eData, 'certFile', eData['workDir'])

  setDefault(eData, 'keyFile', eData['name'] + '-key.pem')
  sanitizeFilePath(eData, 'keyFile', eData['workDir'])

  setDefault(eData, '7zFile', eData['name'] + '.7z')
  sanitizeFilePath(eData, '7zFile', eData['workDir'])

  setDefault(eData, 'keySize',        config['cpf']['keySize'])
  setDefault(eData, 'days',           caData['days'])
  setDefault(eData, 'country',        caData['country'])
  setDefault(eData, 'province',       caData['province'])
  setDefault(eData, 'locality',       caData['locality'])
  setDefault(eData, 'organization',   caData['organization'])
  setDefault(eData, 'federationName', caData['federationName'])
  setDefault(eData, 'serialNum',      caData['serialNum']+eNum)

  generateNewPassword(passwords, eData, config)

  if podDefaults is not None :
    mergePodDefaults(eData, podDefaults)
    setDefault(eData, 'podName',  "{}-{}".format(eData['federationName'], eData['name']))
    eData['imageLocal']  = {}
    eData['imageRemote'] = {}
    for anImage in eData['images'] :
      localImageName = "{}-{}".format(eData['federationName'], anImage).lower()
      eData['imageLocal' ][anImage] = localImageName
      eData['imageRemote'][anImage] = getRegistryFlagAndPath(
        localImageName,
        config['cpf']['registry'])

def normalizeConfig(config) :

  if 'cpf' not in config :
    logging.error("A compute pod federation (cpf) descript MUST be provided!")
    sys.exit(-1)

  if 'federationName' not in config['cpf'] :
    logging.error("A compute pod federation name MUST be provided!")
    sys.exit(-1)

  config['federationName'] = config['cpf']['federationName']

  if 'certificateAuthority' not in config['cpf'] :
    logging.error("A compute pod federation certificate authority MUST be provided!")
    sys.exit(-1)

  caData = config['cpf']['certificateAuthority']
  caData['federationName'] = config['cpf']['federationName']

  if 'validFor' not in caData :
    caData['days'] = 10*366 # just over 10 years
  else :
    validFor = caData['validFor']
    days = 0
    if 'years' in validFor :
      days = days + 366*validFor['years']
    if 'months' in validFor :
      days = days + 31*validFor['months']
    if 'days' in validFor :
      days = days + validFor['days']
    caData['days'] = days

  if 'serialNum' not in caData :
    caData['serialNum'] = int(time.time()) * 10000

  entityNum = 0
  normalizeSslEntity(config, caData, entityNum, 'certificateAuthorityDir', caData, None)
  entityNum += 1

  podDefaults = config['cpf']['podDefaults']

  for aPod in config['cpf']['computePods'] :
    normalizeSslEntity(config, aPod, entityNum, 'podsDir', caData, podDefaults)
    entityNum += 1

  for aUser in config['cpf']['users'] :
    normalizeSslEntity(config, aUser, entityNum, 'usersDir', caData, None)
    entityNum += 1

  config['cpf']['rsync'] = { }
  normalizeSshEntity(config, config['cpf']['rsync'], 'certificateAuthorityDir')

  if config['verbose'] :
    logging.info("configuration:\n------\n" + yaml.dump(config) + "------\n")

############################################################################
# Creation methods

def createWorkDirFor(msg, eData) :
  if not os.path.isdir(eData['workDir']) :
    logging.info("creating the {} {} work directory".format(msg, eData['name']))
    os.makedirs(eData['workDir'], exist_ok=True)

def createSshKeyFor(msg, eData) :
  if os.path.isfile(eData['keyFile']) :
    logging.info("{} {} key file exists -- not recreating".format(msg, eData['name']))
  else :
    cmd = "ssh-keygen -N {} -b {} -t rsa -C {} -f {}".format(
       eData['password'], eData['keySize'], eData['comment'], eData['keyFile'])
    click.echo("\ncreating the {} {} ssh key".format(msg, eData['name']))
    click.echo("-------------------------------")
    click.echo(cmd)
    click.echo("----ssh-key-file-generation----")
    os.system(cmd)
    click.echo("----ssh-key-file-generation----")

def createKeyFor(msg, eData) :
  if os.path.isfile(eData['keyFile']) :
    logging.info("{} {} key file exists -- not recreating".format(msg, eData['name']))
  else :
    cmd = "openssl genpkey -algorithm RSA -out {} -pkeyopt rsa_keygen_bits:{}".format(
      eData['keyFile'], eData['keySize'])
    click.echo("\ncreating the {} {} rsa key".format(msg, eData['name']))
    click.echo("-------------------------------")
    click.echo(cmd)
    click.echo("----rsa-key-file-generation----")
    os.system(cmd)
    click.echo("----rsa-key-file-generation----")

# Cerate a new "base" x509 Certificate (in the openSSL configuration)
# based upon the CA's configured certificate information.
#
#    SignatureAlgorithm: x509.SHA512WithRSA, (command line??)
#    serialNumber (we use unixTimeStamp * 10000 + entityNumber)
#    days on command line (default is 10 366 day years)
#
#    organization
#    organizationalUnitName
#    countryName
#    stateOrProvinceName
#    localityName
#    commonName
#    emailAddresses
#
# Various fields specific to a particular certificate use will still need
# to be filed in by the CA, Nursery, or User certificate code
# respectively.
#
# CA:
#   basicConstraints = CA:TRUE
#   keyUsage         =  nonRepudiation, digitalSignature, keyCertSign, cRLSign
#   nsCertType       = sslCA, objCA
#
# PODS and Users: (all client/servers)
#  nCert.ExtKeyUsage = []x509.ExtKeyUsage{
#      x509.ExtKeyUsageClientAuth,
#      x509.ExtKeyUsageServerAuth,
#    }
#  nCert.SubjectKeyId = []byte{1,2,3,4,6}
#  nCert.KeyUsage = x509.KeyUsageDigitalSignature |
#      x509.KeyUsageKeyEncipherment |
#      x509.KeyUsageKeyAgreement |
#      x509.KeyUsageDataEncipherment
#
#  // Add the DNSNames and IPAddresses
#  for _, aHost := range nursery.Hosts {
#    possibleIPAddress := net.ParseIP(aHost)
#    if possibleIPAddress != nil {
#      nCert.IPAddresses = append(nCert.IPAddresses, possibleIPAddress)
#    } else {
#      nCert.DNSNames = append(nCert.DNSNames, aHost)
#    }
#  }
#
# USERS:
#  uCert.ExtKeyUsage  = []x509.ExtKeyUsage{ x509.ExtKeyUsageClientAuth }
#  uCert.SubjectKeyId = []byte{1,2,3,4,6}
#  uCert.KeyUsage     = x509.KeyUsageDigitalSignature |
#      x509.KeyUsageKeyEncipherment |
#      x509.KeyUsageKeyAgreement |
#      x509.KeyUsageDataEncipherment
#
# It is CRITICAL that we use DIFFERENT serial numbers for each of the:
#  - Certificate Authority:  unixTimeStamp + 0,
#  - Clien/Server:           unixTimeStamp + entityNum (pods first)
#  - User:                   unixTimeStamp + entiryNum (users second)
# certificates. We do this using the "serialNumModifier" parameter. (This
# assumes a maximum of 10,000 pods/users)
#

def createCertFor(msg, certData, caData) :
  if os.path.isfile(certData['sslConfigFile']) :
    logging.info("{} {} openssl configuration file exists -- not recreating".format(msg, certData['name']))
  else :
    click.echo("\ncreating the {} {} openssl configuration".format(msg, certData['name']))
    configReq = [
      "[ req ]",
      "  prompt             = no",
      "  encrypt_key        = no",
      "  distinguished_name = the_dn",
      "  x509_extensions    = the_cert",
    ]
    configDN = [
      "[ the_dn ]",
      "  countryName            = {}".format(certData['country']),
      "  stateOrProvinceName    = {}".format(certData['province']),
      "  localityName           = {}".format(certData['locality']),
      "  organizationName       = {}".format(certData['organization']),
      "  organizationalUnitName = {}".format(certData['federationName']),
      "  commonName             = {}".format(certData['name']),
    ]

    # client/server (both pods and users)
    configCert = [
      "[ the_cert ]",
      "  basicConstraints = CA:FALSE",
      "  keyUsage         = nonRepudiation, digitalSignature, keyAgreement, keyEncipherment",
      "  extendedKeyUsage = serverAuth, clientAuth",
      "  nsCertType       = client, server",
    ]
    if caData is None :
      # certificate authority
      configCert = [
        "[ the_cert ]",
        "  basicConstraints = CA:TRUE",
        "  keyUsage         = nonRepudiation, digitalSignature, keyCertSign, cRLSign",
        "  nsCertType       = sslCA, objCA",
      ]

    configFile = open(certData['sslConfigFile'], "w")
    configFile.write("\n")
    configFile.write("\n".join(configReq))
    configFile.write("\n")
    configFile.write("\n".join(configDN))
    configFile.write("\n")
    configFile.write("\n".join(configCert))
    configFile.write("\n")
    configFile.close()

  if caData is not None :
    if os.path.isfile(certData['csrFile']) :
      logging.info("{} {} certificate signing request file exists -- not recreating".format(msg, certData['name']))
    else :
      # client/server CSR
      # see: https://gist.github.com/nordineb/4e8f9122f6962c33e56f02d0d5794b3d
      #
      cmd = "openssl req -new -key {} -out {} -config {}".format(
        certData['keyFile'], certData['csrFile'], certData['sslConfigFile'])

      click.echo("\ncreating the {} {} certificate signing request file".format(msg, certData['name']))
      click.echo("-------------------------------")
      click.echo(cmd)
      click.echo("----csr-file-generation----")
      os.system(cmd)
      click.echo("----csr-file-generation----")

  if os.path.isfile(certData['certFile']) :
    logging.info("{} {} certificate file exists -- not recreating".format(msg, certData['name']))
  else :
    # self signed CA
    cmd = "openssl req -x509 -key {} -out {} -config {} -days {} -set_serial {}".format(
      certData['keyFile'], certData['certFile'],
      certData['sslConfigFile'], certData['days'],
      certData['serialNum'])
    if caData is not None :
      # client/server Cert (using CSR created above)
      # see: https://gist.github.com/nordineb/4e8f9122f6962c33e56f02d0d5794b3d
      #
      cmd = "openssl x509 -req -in {} -out {} -CA {} -CAkey {} -days {} -set_serial {}".format(
        certData['csrFile'], certData['certFile'],
        caData['certFile'], caData['keyFile'],
        certData['days'], certData['serialNum'])

    click.echo("\ncreating the {} {} certificate file".format(msg, certData['name']))
    click.echo("-------------------------------")
    click.echo(cmd)
    click.echo("----cert-file-generation----")
    os.system(cmd)
    click.echo("----cert-file-generation----")
    click.echo("")

def saveShellScriptTemplate(templateName, theTemplate, templateValues, filePath) :
  try:
    template = jinja2.Template(theTemplate)
    fileContents = template.render(templateValues)
    with open(filePath, 'w') as outFile :
      outFile.write(fileContents)
    os.chmod(filePath,
      stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
      stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
      stat.S_IROTH | stat.S_IXOTH)
  except Exception as err:
    logging.error("Could not render the Jinja2 template [{}]".format(templateName))
    logging.error(err)

def createPod(podData) :

  logging.info("creating the pod {} scripts".format(podData['podName']))

  scriptPaths = []

  podData['podScriptFile'] = podData['name'] + '-create-pod.sh'
  sanitizeFilePath(podData, 'podScriptFile', podData['workDir'])
  scriptPaths.append(podData['podScriptFile'])
  saveShellScriptTemplate(
    'podCreation.sh.j2',
    importlib.resources.read_text('cpb.resources', 'podCreation.sh.j2'),
    podData,
    podData['podScriptFile']
  )

  podData['podScriptFile'] = podData['name'] + '-remove-pod.sh'
  sanitizeFilePath(podData, 'podScriptFile', podData['workDir'])
  scriptPaths.append(podData['podScriptFile'])
  saveShellScriptTemplate(
    'podRemoval.sh.j2',
    importlib.resources.read_text('cpb.resources', 'podRemoval.sh.j2'),
    podData,
    podData['podScriptFile']
  )

  podData['podScriptFile'] = podData['name'] + '-remove-images.sh'
  sanitizeFilePath(podData, 'podScriptFile', podData['workDir'])
  scriptPaths.append(podData['podScriptFile'])
  saveShellScriptTemplate(
    'imageRemoval.sh.j2',
    importlib.resources.read_text('cpb.resources', 'imageRemoval.sh.j2'),
    podData,
    podData['podScriptFile']
  )

  podData['podScriptFile'] = podData['name'] + '-start-pod.sh'
  sanitizeFilePath(podData, 'podScriptFile', podData['workDir'])
  scriptPaths.append(podData['podScriptFile'])
  saveShellScriptTemplate(
    'podStart.sh.j2',
    importlib.resources.read_text('cpb.resources', 'podStart.sh.j2'),
    podData,
    podData['podScriptFile']
  )

  podData['podScriptFile'] = podData['name'] + '-stop-pod.sh'
  sanitizeFilePath(podData, 'podScriptFile', podData['workDir'])
  scriptPaths.append(podData['podScriptFile'])
  saveShellScriptTemplate(
    'podStop.sh.j2',
    importlib.resources.read_text('cpb.resources', 'podStop.sh.j2'),
    podData,
    podData['podScriptFile']
  )

  theTemplate = importlib.resources.read_text('cpb.resources', 'enterContainer.sh.j2')
  for anImage in podData['images'] :
    podData['podScriptFile'] = '{}-enter-{}.sh'.format(podData['name'], anImage)
    sanitizeFilePath(podData, 'podScriptFile', podData['workDir'])
    scriptPaths.append(podData['podScriptFile'])
    saveShellScriptTemplate(
      'enterContainer.sh.j2 ({})'.format(anImage),
      theTemplate,
      { 'podName' : podData['podName'], 'anImage' : anImage },
      podData['podScriptFile']
    )

  # Then 7-zip up the directory...
  with py7zr.SevenZipFile(podData['7zFile'], 'w', password=podData['password']) as zf:
    def saveFile(fileName) :
      zf.write(fileName, arcname=os.path.join('podConfig', os.path.basename(fileName)))
    saveFile(podData['sslConfigFile'])
    saveFile(podData['csrFile'])
    saveFile(podData['certFile'])
    saveFile(podData['keyFile'])
    for aPath in scriptPaths :
      saveFile(aPath)

############################################################################
# Do the work...

@click.command("create")
@click.pass_context
def create(ctx):
  """
  (re)Creates any missing compute pod descriptions.

  """
  config = ctx.obj
  normalizeConfig(config)

  click.echo("\n(re)Creating the {} federation".format(config['cpf']['federationName']))

  click.echo("\nWorking on certificate authority")
  caData = config['cpf']['certificateAuthority']
  createWorkDirFor("certificate authority", caData)
  createKeyFor("certificate authority", caData)
  createCertFor("certificate authority", caData, None)

  createSshKeyFor('rsync', config['cpf']['rsync'])

  for aPod in config['cpf']['computePods'] :
    click.echo("\nWorking on {} pod".format(aPod['name']))
    createWorkDirFor("pod", aPod)
    createKeyFor("pod", aPod)
    createCertFor("pod", aPod, caData)
    createPod(aPod)

  for aUser in config['cpf']['users'] :
    click.echo("\nWorking on {} user".format(aUser['name']))
    createWorkDirFor("user", aUser)
    createKeyFor("user", aUser)
    createCertFor("user", aUser, caData)

  click.echo("")

  passwordsFile = open(config['passwordsYaml'], 'w')
  passwordsFile.write(yaml.dump(config['passwords']))
  passwordsFile.close()
  os.chmod(config['passwordsYaml'], stat.S_IRUSR | stat.S_IWUSR)
