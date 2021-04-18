import os
import os.path
import subprocess
from subprocess import Popen, PIPE
import sys
from threading import Thread
from urllib.parse import urlparse
from urllib.request import urlretrieve
import venv
from typing import *


clientdir = os.path.dirname(os.path.realpath(__file__))
vdir = os.path.join(clientdir, 'venv')
vbin = os.path.join(vdir, 'Scripts' if os.name == 'nt' else 'bin')
vpy = os.path.join(vbin, 'python')

with open(os.path.join(clientdir, 'requirements.txt'), 'r') as f:
    dependencies = f.readlines()
dependencies = [d.strip() for d in dependencies]  # Get rid of newlines from file

# If running Windows, we will also need curses
if os.name == 'nt':
    dependencies.append('windows-curses')


class ExtendedEnvBuilder(venv.EnvBuilder):
    """
    This builder installs setuptools and pip so that you can pip or
    easy_install other packages into the created environment.

    :param progress: If setuptools or pip are installed, the progress of the
                     installation can be monitored by passing a progress
                     callable. If specified, it is called with two
                     arguments: a string indicating some progress, and a
                     context indicating where the string is coming from.
                     The context argument can have one of three values:
                     'main', indicating that it is called from virtualize()
                     itself, and 'stdout' and 'stderr', which are obtained
                     by reading lines from the output streams of a subprocess
                     which is used to install the app.

                     If a callable is not specified, default progress
                     information is output to sys.stderr.
    """

    def __init__(self, *args, **kwargs):
        self.progress = kwargs.pop('progress', None)
        self.verbose = kwargs.pop('verbose', False)
        super().__init__(*args, **kwargs)

    def post_setup(self, context):
        """
        Set up any packages which need to be pre-installed into the
        environment being created.

        :param context: The information for the environment creation request
                        being processed.
        """
        os.environ['VIRTUAL_ENV'] = context.env_dir
        self.install_setuptools(context)
        # Can't install pip without setuptools
        self.install_pip(context)

    def reader(self, stream, context):
        """
        Read lines from a subprocess' output stream and either pass to a progress
        callable (if specified) or write progress information to sys.stderr.
        """
        progress = self.progress
        while True:
            s = stream.readline()
            if not s:
                break
            if progress is not None:
                progress(s, context)
            else:
                if not self.verbose:
                    sys.stderr.write('.')
                else:
                    sys.stderr.write(s.decode('utf-8'))
                sys.stderr.flush()
        stream.close()

    def install_script(self, context, name, url):
        _, _, path, _, _, _ = urlparse(url)
        fn = os.path.split(path)[-1]
        binpath = context.bin_path
        distpath = os.path.join(binpath, fn)
        # Download script into the env's binaries folder
        urlretrieve(url, distpath)
        progress = self.progress
        if self.verbose:
            term = '\n'
        else:
            term = ''
        if progress is not None:
            progress('Installing %s ...%s' % (name, term), 'main')
        else:
            sys.stderr.write('Installing %s ...%s' % (name, term))
            sys.stderr.flush()
        # Install in the env
        args = [context.env_exe, fn]
        p = Popen(args, stdout=PIPE, stderr=PIPE, cwd=binpath)
        t1 = Thread(target=self.reader, args=(p.stdout, 'stdout'))
        t1.start()
        t2 = Thread(target=self.reader, args=(p.stderr, 'stderr'))
        t2.start()
        p.wait()
        t1.join()
        t2.join()
        if progress is not None:
            progress('done.', 'main')
        else:
            sys.stderr.write('done.\n')
        # Clean up - no longer needed
        os.unlink(distpath)

    def install_setuptools(self, context):
        """
        Install setuptools in the environment.

        :param context: The information for the environment creation request
                        being processed.
        """
        url = 'https://bootstrap.pypa.io/ez_setup.py'
        self.install_script(context, 'setuptools', url)
        # clear up the setuptools archive which gets downloaded
        pred = lambda o: o.startswith('setuptools-') and o.endswith('.tar.gz')
        files = filter(pred, os.listdir(context.bin_path))
        for f in files:
            f = os.path.join(context.bin_path, f)
            os.unlink(f)

    def install_pip(self, context):
        """
        Install pip in the environment.

        :param context: The information for the environment creation request
                        being processed.
        """
        url = 'https://bootstrap.pypa.io/get-pip.py'
        self.install_script(context, 'pip', url)


def missing_dependencies() -> List[str]:
    modules = subprocess.check_output([vpy, '-m', 'pip', 'freeze']).splitlines()
    modules = [m.decode('utf-8') for m in modules]
    missing = []

    for d in dependencies:
        if d not in modules:
            missing.append(d)

    return missing


def venv_exists() -> bool:
    try:
        subprocess.run([vpy, "-c" '"exit()"'])
        return True
    except FileNotFoundError:
        return False


def pip_installed() -> bool:
    r = subprocess.run([vpy, '-m', 'pip'], stdout=subprocess.DEVNULL)
    return r.returncode == 0


def configure_venv():
    # Install a virtual environment with pip installed on it
    compatible = True
    if sys.version_info < (3, 3):
        compatible = False
    elif not hasattr(sys, 'base_prefix'):
        compatible = False
    if not compatible:
        raise ValueError('This script is only for use with '
                         'Python 3.3 or later')
    else:
        builder = ExtendedEnvBuilder(symlinks=os.name != 'nt')
        builder.create(vdir)

    # Re-run with the new environment now that pip is installed
    subprocess.run([vpy, clientdir] + sys.argv[1:])
    exit()


if not venv_exists():
    configure_venv()
elif not pip_installed():
    # A virtual environment is configured but it doesn't have pip.
    # Getting rid of it and re-installing is the easiest way to deal.
    import shutil
    shutil.rmtree(vdir)
    configure_venv()

for d in missing_dependencies():
    r = subprocess.run([vpy, '-m', 'pip', 'install', d])



