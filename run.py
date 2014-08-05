#!/usr/bin/env python

"""
lunaport_server.dev
~~~~~~~~~~~~~~~~~~~

Launch single instance of app with debug and autoreload on changes.
**For development only.**
"""

import os
import sys
#import warnings
#warnings.filterwarnings('ignore', category=SyntaxWarning)

from werkzeug.contrib.profiler import ProfilerMiddleware
from werkzeug.contrib import profiler

# Try to use dev conf from current folder by default instead of ENV variable.
DEV_CFG_PATH = 'lunaport_server.local.cfg'
if os.path.isfile(DEV_CFG_PATH):
    os.environ.update({'LUNAPORT_CFG': os.path.abspath(DEV_CFG_PATH)})
else:
    'Tring to find cfg by env var.'


from lunaport_server.wsgi import app


def main():
    host, port = '0.0.0.0', 9090

    if len(sys.argv) == 2:
        port = sys.argv[1]

        if ':' in port:
            host, port = port.split(':')

        port = int(port)

    
    app.run(debug=True, host=host, port=port)
    #action_profile = profiler.make_action(app)

if __name__ == '__main__':
    main()
