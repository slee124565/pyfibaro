#!/usr/bin/env python

import logging
import requests
import json


class HC2APIBase(object):

    astr_dev_id = 'dev_id'
    astr_scene_id = 'scene_id'
    astr_var_name = 'var_name'
    astr_var_value = 'var_value'
    astr_hostname = 'hostname'
    astr_hostport = 'hostport'
    astr_username = 'username'
    astr_password = 'password'
    astr_remote_name = 'remotename'
    astr_config_file = 'config_file'
        
    def __init__(self,args=None,logger=None):
        self.args = args
        self.logger = logger or logging.getLogger(__name__)

        self.hostname = getattr(self.args, self.astr_hostname)
        self.hostport = getattr(self.args, self.astr_hostport)
        self.username = getattr(self.args, self.astr_username)
        self.password = getattr(self.args, self.astr_password)
        self.api_root_url = 'http://{hc2.hostname}:{hc2.hostport}/api'.format(
            hc2=self)
        self.api_url = self.api_root_url

    def names(self):
        """return name list from GET"""

        data_set = self.get(key=None)
        t_names = []
        if type(data_set) is list:
            for entry in data_set:
                if entry.get('name',None):
                    t_names.append(entry.get('name'))
        return t_names
        
    def get(self, key=None, params=None):
        """Implement HC2 HTTP GET API"""
    
        try:
            if key:
                api_url = self.api_url + '/{key}'.format(key=key)
            else:
                api_url = self.api_url

            r = requests.get(api_url,
                             auth=requests.auth.HTTPBasicAuth(
                                 self.username,
                                 self.password))

            if r.status_code == 200:
                self.logger.debug('api content {}'.format(r.content))
                data = r.json()
                self.logger.debug('api data type {}, data {}'.format(type(data), data))
                return data
            else:
                msg = 'hc2 get api ({api_url}) call fail with requests status code {status_code}'.format(
                    api_url=api_url,status_code=r.status_code)
                self.logger.warning(msg)
                self.logger.debug('requests.get fail response content:\n%s' % (r.content))
                return None
        except:
            self.logger.error('{cls.__name__} get func exception'.format(cls=self.__class__), exc_info=True)
            return None
        
    def put(self,key,obj):
        """Implement HC2 HTTP PUT API"""

        try:
            api_url = self.api_url + '/{key}'.format(key=key)
    
            r = requests.put(
                api_url, 
                data=json.dumps(obj),
                auth=requests.auth.HTTPBasicAuth(self.username,self.password)) 

            if r.status_code == 200:
                self.logger.debug('api content %s' % r.content)
                if r.content.strip() != '':
                    data = r.json()
                    self.logger.debug('api data type %s' % type(data))
                    return data
                else:
                    self.logger.warning('api content empty, nothing to return')
                    return True
            else:
                msg = 'hc2 put api ({api_url}) call fail with requests status code {status_code}'.format(
                    api_url=api_url,status_code=r.status_code)
                self.logger.warning(msg)
                self.logger.debug('requests.put fail response content:\n%s' % (r.content))
                return None
        except:
            self.logger.error('{cls.__name__} put func exception'.format(cls=self.__class__), exc_info=True)
            return None
        
        
    def post(self,obj):
        """Implement HC2 HTTP POST API"""

        try:
            api_url = self.api_url
    
            r = requests.post(
                api_url, 
                data=json.dumps(obj),
                auth=requests.auth.HTTPBasicAuth(self.username,self.password)) 

            if r.status_code in range(200,300):
                data = r.json()
                self.logger.debug('api data type %s' % type(data))
                return data
            else:
                msg = 'hc2 post api ({api_url}) call fail with requests status code {status_code}'.format(
                    api_url=api_url,status_code=r.status_code)
                self.logger.warning(msg)
                self.logger.debug('requests.post fail response content:\n%s' % (r.content))
                return None
        except:
            self.logger.error('{cls.__name__} post func exception'.format(cls=self.__class__), exc_info=True)
            return None

    def delete(self,key):
        """Implement HC2 HTTP POST API"""

        try:
            api_url = self.api_url + '/{key}'.format(key=key)
    
            r = requests.delete(
                api_url, 
                auth=requests.auth.HTTPBasicAuth(self.username,self.password)) 

            if r.status_code in range(200,300):
                #data = r.json()
                data = r.content
                self.logger.debug('api data type %s' % type(data))
                return data
            else:
                msg = 'hc2 delete api ({api_url}) call fail with requests status code {status_code}'.format(
                    api_url=api_url,status_code=r.status_code)
                self.logger.warning(msg)
                self.logger.debug('requests.delete fail response content:\n%s' % (r.content))
                return None
        except:
            self.logger.error('{cls.__name__} delete func exception'.format(cls=self.__class__), exc_info=True)
            return None
        
    @classmethod
    def main(cls):
        """"""
        # test hc2
#         HC2_IP = '192.168.1.10'
#         HC2_PORT = 80
#         HC2_USERNAME = 'tailungfu@gmail.com'
#         HC2_PASSWORD = 'FLHflhtest12345'
        
        # showroom hc2
        HC2_IP = '192.168.10.5'
        HC2_PORT = 80
        HC2_USERNAME = 'service@flh.com.tw'
        HC2_PASSWORD = 'FLHflhtest12345'

        import argparse
        
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
      
        parser.add_argument(
            '--debug',
            action='store_true',
            help='print debug message',
            default=False)
      
        parser.add_argument(
            '--print_result',
            action='store_true',
            help='print command function result',
            default=False)
      
        parser.add_argument(
            '--username',
            help='hc2 username for login, default: %(default)s',
            default=HC2_USERNAME)
          
        parser.add_argument(
            '--password',
            help='hc2 password for login, default: %(default)s',
            default=HC2_PASSWORD)
          
        parser.add_argument(
            '--hostname',
            help='hc2 hostname or IP for login, default: %(default)s',
            default=HC2_IP)
          
        parser.add_argument(
            '--hostport',
            help='hc2 web api port for access, default: %(default)s',
            default=HC2_PORT)
      
        parser.add_argument(
            'command',
            help='class pi function name and args (cmd,arg,...) as command to be executed',
            default=None)
    
        args = parser.parse_args()
        
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    
        if args.debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
            logging.getLogger("requests").setLevel(logging.WARNING)
    
        logger = logging.getLogger()    
        logger.setLevel(log_level)
        logger.debug('args: %s' % str(args))
        hc2 = cls(args=args,logger=logger)
        try :
            hc2.logger.info('exec {cls.__name__} API cmd_args : {args}'.format(
                cls=cls,args=args.command))
            params = args.command.split(',')
            func_name = params[0]
            if len(params) > 1:
                func_args = params[1:]
                
            cmd_func = getattr(hc2, func_name)
            if len(params) == 1: # func with no args
                result = cmd_func()
            else:
                result = cmd_func(*tuple(func_args))
            if args.print_result:
                hc2.logger.info(result)
            else:
                hc2.logger.info('== done ==')
        except:
            hc2.logger.error('exec HomeCenter2 API cmd error',exc_info=True ) 
        
        
if __name__ == '__main__':
    HC2APIBase.main()
        

        
