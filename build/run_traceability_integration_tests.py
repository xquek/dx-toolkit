#!/usr/bin/env python

'''
Runs Python integration tests tagged for inclusion in the traceability matrix.
'''

from __future__ import print_function, unicode_literals

import os
import platform
import subprocess
import sys

TOOLKIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
PYTHON_DIR = os.path.join(TOOLKIT_ROOT_DIR, 'src', 'python')
PYTHON_TEST_DIR = os.path.join(PYTHON_DIR, 'test')

os.environ['DNANEXUS_INSTALL_PYTHON_TEST_DEPS'] = 'yes'
os.environ['DX_USER_CONF_DIR'] = TOOLKIT_ROOT_DIR + "/dnanexus_config_relocated"

def run():
    # src_libs is to ensure that dx-unpack is runnable. If we had "bash unit
    # tests" that were broken out separately, that would obviate this though.
    #
    # Note that Macs must run the make command before running this script,
    # as of b9d8487 (when virtualenv was added to the Mac dx-toolkit release).
    if sys.platform != "darwin":
        subprocess.check_call(["make", "python", "src_libs"], cwd=TOOLKIT_ROOT_DIR)

    # Somewhat hacky-- ensures that all subprocess calls to dx-* tools
    # load the coverage instrumentation so that their use of dxpy is
    # reflected in the final report.
    site_customize_filename = os.path.join(TOOLKIT_ROOT_DIR, 'share', 'dnanexus', 'lib', 'python2.7', 'site-packages', 'sitecustomize.py')
    with open(site_customize_filename, 'w') as site_customize_file:
        site_customize_file.write("import coverage; coverage.process_startup()\n")
    try:
        subprocess.check_call("rm -vf .coverage .coverage.*", cwd=PYTHON_DIR, shell=True)

        #cmd = ['python', '-m', 'unittest']
        #if args.tests:
        #    cmd += ['-v'] + args.tests
        #else:
        #    cmd += ['discover', '--start-directory', '.', '--verbose']
        cmd = ['py.test', '-vv', '-s', '-m', 'TRACEABILITY_MATRIX', 'src/python/test/']

        subproc_env = dict(os.environ)

        # Setting COVERAGE_PROCESS_START is required to collect coverage for
        # subprocess calls to dx.py and friends. Also, wrap values in str()
        # to avoid "environment can only contain strings" error on Windows:
        subproc_env[str('COVERAGE_PROCESS_START')] = str(os.path.join(PYTHON_DIR, '.coveragerc'))
        subproc_env[str('COVERAGE_FILE')] = str(os.path.join(PYTHON_DIR, '.coverage'))

        try:
            subprocess.check_call(cmd, cwd=TOOLKIT_ROOT_DIR, env=subproc_env)
        except subprocess.CalledProcessError as e:
            print('*** unittest invocation failed with code %d' % (e.returncode,), file=sys.stderr)
            sys.exit(1)

        try:
            subprocess.check_call(["coverage", "combine"], cwd=PYTHON_DIR)
        except subprocess.CalledProcessError as e:
            print('*** coverage invocation failed with code %d' % (e.returncode,), file=sys.stderr)
            sys.exit(1)
        except OSError:
            print("*** coverage invocation failed: no coverage file found; please install coverage v3.7.1",
                  file=sys.stderr)
    finally:
        os.unlink(site_customize_filename)

if __name__ == '__main__':
    run()
