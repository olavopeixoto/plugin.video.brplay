# -*- coding: utf-8 -*-

import sys
from resources.lib import main
from resources.lib.modules import control
import urllib.parse as urlparse
import buggalo


if __name__ == '__main__':
    try:
        control.log('%s %s | Starting...' % (control.addonInfo('name'), control.addonInfo('version')))

        buggalo.EMAIL_CONFIG = {
                "recipient": 'brplayissues@gmail.com',
                "sender": "BRplay <brplayissues@gmail.com>",
                "server": 'smtp.googlemail.com',
                "method": 'ssl',
                "user": 'brplayissues@gmail.com',
                "pass": "yourpasswordforbuggalo_account"
            }

        argv = dict(urlparse.parse_qsl(sys.argv[2].replace('?', '')))

        main.run(argv)

    except Exception:
        buggalo.onExceptionRaised()

    finally:
        control.log("Finished Processing")
