'''
Command Tool for HC2 Global Variables
'''

import json
import sys

from cmd_base import CMDBase

class CMDVariable(CMDBase):

    @classmethod
    def cmd_list(cls,args):
        '''list all global variable name from hc2'''
        hc2 = cls.get_args_hc2(args)
        hc2.gvar_list()

    @classmethod
    def cmd_query(cls,args):
        '''query variable value from hc2'''
        hc2 = cls.get_args_hc2(args)
        var_name = getattr(args, cls.astr_var_name)
        var = hc2.gvar_query(var_name)
        if var:
            sys.stderr.write('%s\n' % json.dumps(var,indent=2))
        else:
            sys.stderr.write('global variable %s not exist\n' % (var_name))
        
    @classmethod
    def cmd_create(cls,args):
        '''query variable value from hc2'''
        hc2 = cls.get_args_hc2(args)
        var_name = getattr(args, cls.astr_var_name)
        var_value = getattr(args, cls.astr_var_value)
        t_var = {
                  "name": var_name, 
                  "value": var_value, 
                }
        var = hc2.gvar_create(t_var)
        if var:
            sys.stderr.write('%s\n' % json.dumps(var,indent=2))
        else:
            sys.stderr.write('fail to create hc2 global variable %s\n' % (var_name))

    @classmethod
    def cmd_delete(cls,args):
        '''query variable value from hc2'''
        hc2 = cls.get_args_hc2(args)
        var_name = getattr(args, cls.astr_var_name)
        hc2.gvar_delete(var_name)
        var = hc2.gvar_query(var_name)
        if var:
            sys.stderr.write('fail to delete hc2 global variable %s\n' % (var_name))
        else:
            sys.stderr.write('success to delete hc2 global variable %s\n' % json.dumps(var,indent=2))

    @classmethod
    def cmd_update(cls,args):
        '''query variable value from hc2'''
        hc2 = cls.get_args_hc2(args)
        var_name = getattr(args, cls.astr_var_name)
        var_value = getattr(args, cls.astr_var_value)
        t_var = {
                  "name": var_name, 
                  "value": var_value, 
                }
        var = hc2.gvar_update(var_name,t_var)
        if var:
            sys.stderr.write('%s\n' % json.dumps(var,indent=2))
        else:
            sys.stderr.write('fail to create hc2 global variable %s\n' % (var_name))

    @classmethod
    def cmd_pull(cls,args):
        '''query and save variable value from hc2'''
        hc2 = cls.get_args_hc2(args)
        var_name = getattr(args, cls.astr_var_name)
        var = hc2.gvar_pull(var_name)
        if var:
            sys.stderr.write('%s\n' % json.dumps(var,indent=2))
        else:
            sys.stderr.write('global variable %s not exist\n' % (var_name))

    @classmethod
    def cmd_push(cls,args):
        '''update hc2 global variable with local dumped file'''
        hc2 = cls.get_args_hc2(args)
        var_name = getattr(args, cls.astr_var_name)
        var = hc2.gvar_push(var_name)
        if var:
            sys.stderr.write('%s\n' % json.dumps(var,indent=2))
        else:
            sys.stderr.write('global variable %s not exist\n' % (var_name))

    @classmethod
    def get_cmd_parser(cls,base_parser,subparsers):
        cmd_parser = subparsers.add_parser(
            'gvar',
            description=__doc__,
            help='hc2 global variables command tool',
            parents=[base_parser])
        
        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')
        
        # var list
        scmd_parser = scmd_subparsers.add_parser(
            'list',
            help='list all variable value from hc2',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_list)

        # var query
        scmd_parser = scmd_subparsers.add_parser(
            'query',
            help='query variable value from hc2',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_var_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_query)
        
        # var create
        scmd_parser = scmd_subparsers.add_parser(
            'create',
            help='create hc2 global variable',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_var_name(scmd_parser)
        cls.add_parser_arg_var_value(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_create)
        
        # var update
        scmd_parser = scmd_subparsers.add_parser(
            'update',
            help='update hc2 global variable value',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_var_name(scmd_parser)
        cls.add_parser_arg_var_value(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_update)

        # var delete
        scmd_parser = scmd_subparsers.add_parser(
            'delete',
            help='delete hc2 global variable',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_var_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_delete)

        # var pull
        scmd_parser = scmd_subparsers.add_parser(
            'pull',
            help='pull hc2 global variable',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_var_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_pull)

        # var push
        scmd_parser = scmd_subparsers.add_parser(
            'push',
            help='push hc2 global variable',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_var_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_push)

        return cmd_parser
