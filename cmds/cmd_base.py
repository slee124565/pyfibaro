
import argparse


class CMDBase(object):

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
    astr_pi_ip = 'pi_ip'
    astr_pi_port = 'pi_port'
    astr_modbus_id = 'modbus_id'
    astr_hc2_service = 'hc2_api'
    
    # -- common functions for all CMDBase
    @classmethod
    def set_args_hc2(cls, args, hc2=None):
        """add HC2 API Server object into args object attribute"""
        setattr(args, cls.astr_hc2_service, hc2)
    
    @classmethod
    def get_args_hc2(cls, args):
        hc2 = getattr(args, cls.astr_hc2_service, None)
        return hc2
    
    @classmethod
    def get_hc2_from_args(cls, args):
        hc2 = getattr(args, cls.astr_hc2_service)    
        return hc2
        
    # -- common args functions for all CMDBase
    @classmethod
    def get_base_parser(cls):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            add_help=False)
     
        parser.add_argument(
            '--debug',
            action='store_true',
            help='print debug message',
            default=False)
        return parser

    @classmethod
    def add_parser_arg_dev_id(cls, parser):
        parser.add_argument(
            cls.astr_dev_id,
            type=int,
            help='hc2 device id')

    @classmethod
    def add_parser_arg_scene_id(cls, parser):
        parser.add_argument(
            cls.astr_scene_id,
            type=int,
            help='hc2 scene id')

    @classmethod
    def add_parser_arg_var_name(cls, parser):
        parser.add_argument(
            cls.astr_var_name,
            help='hc2 global variable name')
    
    @classmethod
    def add_parser_arg_var_value(cls, parser):
        parser.add_argument(
            cls.astr_var_value,
            help='hc2 global variable value')


    @classmethod
    def add_parser_arg_hostname(cls, parser):
        parser.add_argument(
            cls.astr_hostname,
            help='hc2 hostname config value')

    @classmethod
    def add_parser_arg_hostport(cls, parser):
        parser.add_argument(
            cls.astr_hostport,
            type=int,
            help='hc2 hostport config value')

    @classmethod
    def add_parser_arg_username(cls, parser):
        parser.add_argument(
            cls.astr_username,
            help='hc2 account username config value')

    @classmethod
    def add_parser_arg_password(cls, parser):
        parser.add_argument(
            cls.astr_password,
            help='hc2 account password config value')

    @classmethod
    def add_parser_arg_remote_name(cls, parser):
        parser.add_argument(
            cls.astr_remote_name,
            help='remote hc2 name text')
        
    @classmethod
    def add_parser_arg_pi_ip(cls, parser):
        parser.add_argument(
            cls.astr_pi_ip,
            help='raspbery pi ip address')
        
    @classmethod
    def add_parser_arg_pi_port(cls, parser):
        parser.add_argument(
            cls.astr_pi_port,
            type=int,
            help='raspbery pi listen socket port')

    @classmethod
    def add_parser_arg_modbus_id(cls, parser):
        parser.add_argument(
            cls.astr_modbus_id,
            type=int,
            help='modbus id address')

