
import sys, os
import logging
import json
import shutil

CONFIG_FILE_DEFAULT = '.hc2_config'


class RemoteCollection(object):
    remotes = {}
    
    def __init__(self, args=None, logger=None):
        self.args = args
        self.logger = logger or logging.getLogger(__name__)
        self._load_config_file()
        
    # __getitem__ implement start
    def __getitem__(self, key):
        self._load_config_file()
        if key in self.remotes.keys():
            return self.remotes[key]
        else:
            #sys.stdout.write('remote name %s not exist\n\n' % key)
            #sys.exit(2)
            return None

    def __setitem__(self, key, value):
        self.remotes[key] = value
        self._save_config_file()
        
    def __delitem__(self, key):
        if key in self.remotes.keys():
            self.remotes.pop(key)
            self._save_config_file()
        else:
            sys.stderr.write('remote %s not existing in config\n' % key)

    def _get_config_file_path(self):
        if os.path.exists('/usr/share/flh'):
            config_path = os.path.join('/usr/share/flh', CONFIG_FILE_DEFAULT)
        elif os.path.exists('/Users/lee_shiueh/flh/projects/common'):
            config_path = os.path.join('/Users/lee_shiueh/flh/projects/common', CONFIG_FILE_DEFAULT)
        else:
            config_path = os.path.join(os.getcwd(), CONFIG_FILE_DEFAULT)

        self.logger.debug('{} _get_config_file_path {}'.format(self.__class__.__name__, config_path))
        return config_path

    def _save_config_file(self):
        config_path = self._get_config_file_path()
        tmp_config_path = os.path.join(os.getcwd(), CONFIG_FILE_DEFAULT + '.tmp')
        with open(tmp_config_path, 'wb') as fh:
            fh.write(json.dumps(self.remotes, indent=2))
        shutil.move(tmp_config_path, config_path)
        
    def _load_config_file(self):
        # config_path = os.path.join(os.getcwd(), CONFIG_FILE_DEFAULT)
        config_path = self._get_config_file_path()
        if not os.path.exists(config_path):
            #sys.stderr.write('tool needs to be configured in advance, use [add remote] command\n')
            #raise Exception('HC2 Remote Init Error, %s' % msg)
            self._save_config_file()
        else:
            with open(config_path) as fh:
                self.remotes = json.loads(fh.read())
        
        return self.remotes
        

