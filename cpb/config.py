# This python3 click subcommand lists the configuration of a cpb compute pod

import click
import yaml

def normalizeConfig(config) :
  pass
    
@click.command()
@click.pass_context
def config(ctx):
  """
  List the current configuration and global options.

  This command can be used to list the currently known configuration 
  key/values for a given cpb.

  This command can also be used to list (potential) additional global 
  configuration parameters you might like to specify. 
  """ 

  print("configuration:\n------\n" + yaml.dump(ctx.obj) + "------\n")

  click.echo("""
The following configuration options can be specified in the global YAML 
configuraiton file.

This global configuration file is by default located in the file 

        ~/.config/cpb/config.yaml

however you can use the `--config` option on the command line to specify a 
different path. 

The configuration options which can be over-ridden on the command line 
have their command line switches listed in brackets. 

--------------------------------------------------------------------------

commonsDir:

    The path to the commons directories mounted inside each cpb container 
    as `/commons`. This path is as it will be found on the host machine, 
    and may be either absolute or relative to the user's home directory 
    (~/commons). 

imageYaml:

    The name of the image.yaml file used by cekit to describe how to build 
    the cpb container image. 
    
cpbYaml:

    The name of the cpb.yaml file used by cpb to describe how to run a cpb 
    container image. 

cekitConfig: 

    The name of the global INI configuration as used by our use of cekit. 
    If this option does not begin with a '/', then it assumed to be a path 
    relative to the configPath directory. 
        
verbose: (-v, --verbose)

    A boolean which specifies if additional working details should be 
    reported on the standard output. 
  """)
