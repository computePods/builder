# This python3 click subcommand creates a new pde commons area

import click
import glob
import jinja2
import logging
import os
import shutil
import time
import yaml

from cpb.utils import *

# We use openssl from the command line...
# 
# See: https://www.openssl.org/docs/manmaster/man5/x509v3_config.html
# 
# Examples: 
#   https://megamorf.gitlab.io/cheat-sheets/openssl/
#   https://access.redhat.com/solutions/28965
#   https://gist.github.com/thisismitch/bf52b0c1823da27ff353
#

def setDefault(eData, key, value) :
  if key not in eData :
    eData[key] = value

def normalizeEntity(config, eData, eNum, workDirKey, caData) :
  if workDirKey == 'certificateAuthorityDir' :
    if 'federationName' not in eData :
      logging.error("All certificate authorities MUST have a 'federationName' key")
      sys.exit(-1)
    eData['name'] = eData['federationName'] + '-ca'
  if workDirKey == 'podsDir' :
    if 'host' not in eData :
      logging.error("All pods MUST have a 'host' key")
      sys.exit(-1)
    eData['name'] = eData['host'].split(',')[0]
  if workDirKey == 'usersDir' :
    if 'name' not in eData :
      logging.error("All users MUST have a 'name' key")
      sys.exit(-1)

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

  setDefault(eData, 'keySize',        config['cpf']['keySize'])
  setDefault(eData, 'days',           caData['days'])
  setDefault(eData, 'country',        caData['country'])
  setDefault(eData, 'province',       caData['province'])
  setDefault(eData, 'locality',       caData['locality'])
  setDefault(eData, 'organization',   caData['organization'])
  setDefault(eData, 'federationName', caData['federationName'])
  setDefault(eData, 'serialNum',      caData['serialNum']+eNum)
  
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
  normalizeEntity(config, caData, entityNum, 'certificateAuthorityDir', caData)
  entityNum += 1

  for aPod in config['cpf']['computePods'] :
    normalizeEntity(config, aPod, entityNum, 'podsDir', caData)
    entityNum += 1

  for aUser in config['cpf']['users'] :
    normalizeEntity(config, aUser, entityNum, 'usersDir', caData)
    entityNum += 1
  
  if config['verbose'] :
    logging.info("configuration:\n------\n" + yaml.dump(config) + "------\n")

# see: https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl
def createWorkDirFor(msg, eData) :
  if not os.path.isdir(eData['workDir']) :
    logging.info("creating the {} {} work directory".format(msg, eData['name']))
    os.makedirs(eData['workDir'], exist_ok=True)

def createKeyFor(msg, eData) :
  if os.path.isfile(eData['keyFile']) :
    logging.info("{} key file exists -- not recreating".format(msg))
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
#    serialNumber ?? 
#    days on command line
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
# see: https://www.openssl.org/docs/manmaster/man5/x509v3_config.html
#
# CA: 
#   basicConstraints = CA:TRUE
#   keyUsage         =  nonRepudiation, digitalSignature
#   nsCertType       = sslCA, objCA
#
# PODS:
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
#  - Certificate Authority:  1,
#  - Clien/Server:           (1<<5) + nurseryNum, and
#  - User:                   (2<<5) + userNum
# certificates. We do this using the "serialNumModifier" parameter. (This 
# assumes a maximum of 2^5 - 1 = 31 nurseries or 2^6 - 1 = 63 users) 
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
      # use openssl x509 with one or more of the -CA options
      # OR use openssl req with one or more of the -CA options
      # Seems to NEED two step...
      #  ... create csr with openssl req and then
      #  ... sign it with openssl x509 :-(
      #
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
      # client/server CSR
      # use openssl x509 with one or more of the -CA options
      # OR use openssl req with one or more of the -CA options
      # Seems to NEED two step...
      #  ... create csr with openssl req and then
      #  ... sign it with openssl x509 :-(
      #
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
  createCertFor("certificate authority", caData, None)
  
  for aPod in config['cpf']['computePods'] :
    createWorkDirFor("pod", aPod)
    createKeyFor("pod", aPod)
    createCertFor("pod", aPod, caData)

  for aUser in config['cpf']['users'] :
    createWorkDirFor("user", aUser)
    createKeyFor("user", aUser)
    createCertFor("user", aUser, caData)
