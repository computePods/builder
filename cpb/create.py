# This python3 click subcommand creates a new pde commons area

import click
import glob
import jinja2
import logging
import os
import shutil
import yaml

from cpb.utils import *

def normalizeConfigSection(config, configSection, workDirKey) :
  if workDirKey == 'certificateAuthorityDir' :
    if 'federationName' not in configSection :
      logging.error("All certificate authorities MUST have a 'federationName' key")
      sys.exit(-1)
    configSection['name'] = configSection['federationName']
  if workDirKey == 'podsDir' :
    if 'host' not in configSection :
      logging.error("All pods MUST have a 'host' key")
      sys.exit(-1)
    configSection['name'] = configSection['host'].split(',')[0]
  if workDirKey == 'usersDir' :
    if 'name' not in configSection :
      logging.error("All users MUST have a 'name' key")
      sys.exit(-1)
      
  configSection['workDir'] = os.path.join(config[workDirKey], configSection['name'].replace(" ",""))
  
  if 'sslConfigFile' not in configSection :
    configSection['sslConfigFile'] = config['federationName'] + '-ca.conf'
  sanitizeFilePath(configSection, 'sslConfigFile', configSection['workDir'])

  if 'certFile' not in config :
    configSection['certFile'] = config['federationName'] + '-ca-crt.pem'
  sanitizeFilePath(configSection, 'certFile', configSection['workDir'])

  if 'keyFile' not in config :
    configSection['keyFile']  = config['federationName'] + '-ca-key.pem'
  sanitizeFilePath(configSection, 'keyFile', configSection['workDir'])

  if 'keySize' not in configSection :
    configSection['keySize'] = config['cpf']['keySize']

def normalizeConfig(config) :
  config['federationName'] = config['cpf']['federationName']

  if 'cpf' not in config :
    logging.error("A compute pod federation (cpf) descript MUST be provided!")
    sys.exit(-1)

  if 'federationName' not in config['cpf'] :
    logging.error("A compute pod federation name MUST be provided!")
    sys.exit(-1)

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

  normalizeConfigSection(config, caData, 'certificateAuthorityDir')

  for aPod in config['cpf']['computePods'] :
    normalizeConfigSection(config, aPod, 'podsDir')

  for aUser in config['cpf']['users'] :
    normalizeConfigSection(config, aUser, 'usersDir')
  
  if config['verbose'] :
    logging.info("configuration:\n------\n" + yaml.dump(config) + "------\n")

# see: https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl
def createWorkDirFor(msg, configSection) :
  if not os.path.isdir(configSection['workDir']) :
    logging.info("creating the {} {} work directory".format(msg, configSection['name']))
    os.makedirs(configSection['workDir'], exist_ok=True)

def createKeyFor(msg, configSection) :
  if os.path.isfile(configSection['keyFile']) :
    logging.info("{} key file exists -- not recreating".format(msg))
  else :
    cmd = "openssl genpkey -algorithm RSA -out {} -pkeyopt rsa_keygen_bits:{}".format(
      configSection['keyFile'], configSection['keySize'])
    click.echo("\ncreating the {} {} rsa key".format(msg, configSection['name']))
    click.echo("-------------------------------")
    click.echo(cmd)
    click.echo("----rsa-key-file-generation----")
    os.system(cmd)
    click.echo("----rsa-key-file-generation----")

def createCertFor(msg, certData) :
  if os.path.isfile(certData['sslConfigFile']) :
    logging.info("{} {} openssl configuration file exists -- not recreating".format(msg, certData['name']))
  else :
    click.echo("\ncreating the {} {} openssl configuration".format(msg, certData['name']))
    config = [
      "",
      "[ req ]",
      "  prompt             = no",
      "  encrypt_key        = no",
      "  distinguished_name = {}_details".format(certData['name']),
      "",
      "[ {}_details ]".format(certData['name']),
      "  countryName            = {}".format(certData['country']),
      "  stateOrProvinceName    = {}".format(certData['province']),
      "  localityName           = {}".format(certData['locality']),
      "  organizationName       = {}".format(certData['organization']),
      "  organizationalUnitName = {}".format(certData['federationName']),
      "  commonName             = {}".format(certData['name']),
      ""
    ]
    configFile = open(certData['sslConfigFile'], "w")
    configFile.write("\n".join(config))
    configFile.close()

  if os.path.isfile(certData['certFile']) :
    logging.info("{} {} certificate file exists -- not recreating".format(msg, certData['name']))
  else :
    cmd = "openssl req -x509 -key {} -out {} -config {} -days {}".format(
      certData['keyFile'], certData['certFile'], certData['sslConfigFile'], certData['days'])
    click.echo("\ncreating the {} {} certificate file".format(msg, certData['name']))
    click.echo("-------------------------------")
    click.echo(cmd)
    click.echo("----cert-file-generation----")
    os.system(cmd)
    click.echo("----cert-file-generation----")

@click.command("create")
@click.pass_context
def create(ctx):
  """
  (re)Creates any missing compute pod descriptions.

  """
  config = ctx.obj
  normalizeConfig(config)
  
  click.echo("(re)Creating the {} federation".format(config['cpf']['federationName']))

  caData = config['cpf']['certificateAuthority']
  createWorkDirFor("certificate authority", caData)
  createKeyFor("certificate authority", caData)
  createCertFor("certificate authority", caData)
  
  for aPod in config['cpf']['computePods'] :
    createWorkDirFor("pod", aPod)
    createKeyFor("pod", aPod)
    createCertFor("pod", aPod)

  for aUser in config['cpf']['users'] :
    createWorkDirFor("user", aUser)
    createKeyFor("user", aUser)
    createCertFor("user", aUser)
