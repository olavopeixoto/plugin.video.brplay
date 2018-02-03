# -*- coding: utf-8 -*-

import sys
from resources.lib.main import Main
from resources.lib.modules import control


control.log("Starting...")
main = Main()
main.run(sys.argv[2].replace('?',''))
control.log("Finished Processing")