#/usr/bin/env python3

import distutils.log
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from setuptools.command.install import install

# ---------------------------------------------------------------------------

class PostProcess(install):
    def run(self):
        install.run(self)

#        import pkg_resources

#DATA_PATH = pkg_resources.resource_filename('<package name>', 'data/')
#DB_FILE = pkg_resources.resource_filename('<package name>', 'data/sqlite.db')

        # PyCN stuff: add symbolic links
        dump_exe_files = []
        home_bin_dir = None
        for fn in self.get_outputs():
            ht = os.path.split(fn)
            if not home_bin_dir and ht[1] == 'cli.py':
                home_bin_dir = os.path.split(ht[0])[0] + '/bin/'
            if os.path.split(ht[0])[1] == 'bin':
                dump_exe_files.append(fn)
        self.announce('creating directory ' + home_bin_dir,
                      level = distutils.log.INFO)
        try:
            os.mkdir(home_bin_dir)
        except:
            pass
        for fn in dump_exe_files:
            self.announce('moving %s to %s' % (fn, home_bin_dir),
                      level = distutils.log.INFO)
            os.rename(fn, home_bin_dir + '/' + os.path.split(fn)[1])
        for i in ['fetch.py', 'repo_ls.py', 'repo_put.py']:
            fn = home_bin_dir + i
            self.announce('creating link %s -> %s' % (fn, '../client/cli.py'),
                      level = distutils.log.INFO)
            try:
                os.remove(fn)
            except:
                pass
            os.symlink('../client/cli.py', fn)
        for i in ['srv_fwd.py', 'srv_fwdrepo.py', 'src_repo.py']:
            fn = home_bin_dir + i
            self.announce('creating link %s -> %s' % (fn, '../server/cli.py'),
                      level = distutils.log.INFO)
            try:
                os.remove(fn)
            except:
                pass
            os.symlink('../server/cli.py', fn)

# ---------------------------------------------------------------------------

setup(name            = 'PyCN-lite',
      description     = 'A lightweight implementation of the two '\
                        'ICN protocols NDN and CCNx which also runs '\
                        'under Micropython v1.9.3 for IoT devices ' \
                        'like the ESP8266',
      version         = '0.1.0',
      author          = 'Christian Tschudin',
      download_url    = 'https://github.com/cn-uofbasel/PyCN-lite',
      python_requires = '>=3.0',
      packages        = [
          'pycn_lite.client',
          'pycn_lite.lib',
          'pycn_lite.lib.suite',
          'pycn_lite.server'
      ],
      # package_data={
      #    'bin' : ['bin/dump_*.py'],
      #},
      platforms       = ['UNIX', 'POSIX', 'BSD', 'MacOS 10.X', 'Linux',
                         'Micropython'],
      license         = 'BSD 3-clause',
      data_files      = [('bin', ['pycn_lite/bin/dump_ndn2013.py',
                                  'pycn_lite/bin/dump_ccnx2015.py'])],
      # cmdclass        = { 'build': my_build },
      cmdclass        = { 'install': PostProcess}
)

# eof
