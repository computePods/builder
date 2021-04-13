# This python3 click subcommand creates a new pde commons area

import click
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

############################################################################
# Do the work...

@click.command("build")
@click.pass_context
def build(ctx):
  """
  uses CEKit to build podman images used by this computePod.

  """
  pass
