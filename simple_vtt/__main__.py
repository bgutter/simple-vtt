"""
__main__.py

Module main code

Executed via python -m simple_vtt
"""

import argparse
import sys

from simple_vtt.qt import *

# Parse command line arguments
# Be careful not to step on anything Qt uses in their CLI args
parser = argparse.ArgumentParser( description="A Naive Voice-to-Text System" )
#parser.add_argument( "--mu",    type=int, help="Mean of random-normal data." )
#parser.add_argument( "--sigma", type=int, help="Standard Deviation of random-normal data." )
kwargs = { k: v for k, v in vars( parser.parse_args() ).items() if v is not None }

# Create and run app
app = SimpleVoiceToTextApplication( **kwargs )
sys.exit( app.exec_() )
