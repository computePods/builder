# This is the ComputePodsBuilder (cpb) package

import click
import logging
import os
import sys
import yaml

@click.group()
@click.option("-v", "--verbose",
  help="Provide more diagnostic output.",
  default=False, is_flag=True)
@click.option("--config", "config_file",
  help="The path to the global pde configuration file.",
  default="~/.config/pde/config.yaml", show_default=True)
@click.argument('cpb_name')
@click.pass_context
def cli(ctx, cpb_name, config_file, verbose):
  """
    CPB_NAME is the name of the pde container on which subsequent commands will work.

    The pde subcommands (listed below) come in a number of pairs:

      config : used to view the configuration parameters as seen by pde,

      create/destroy : used to manage the "commons" area as well as image and pde descriptions,

      build/remove : used to manage the podman images used by a running container, 

      start/stop : used to manage the running container used for development, 

      enter : used to enter an already running conainter using the configured shell [default=bash] (this command may be used multiple times). 

      run : used to run a single command in an already running conainter. 

    For details on all other configuration parameters type:

        pde <<pdeName>> config
  """
  ctx.ensure_object(dict)
  # ctx.obj = loadConfig(pde_name, config_file, verbose)

#cli.add_command(pde.build.build)
#cli.add_command(pde.config.config)
#cli.add_command(pde.create.create)
#cli.add_command(pde.destroy.destroy)
#cli.add_command(pde.enter.enter)
#cli.add_command(pde.lists.images)
#cli.add_command(pde.lists.containers)
#cli.add_command(pde.remove.remove)
#cli.add_command(pde.run.run)
#cli.add_command(pde.start.start)
#cli.add_command(pde.stop.stop)
