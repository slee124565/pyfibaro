'''
Command Tool for Serialbox SAPORO AirConditioner or Dehumidifier on HC2
'''

import os
import json
import sys

from cmd_base import CMDBase
    
class CMDSaporo(CMDBase):
    
    repo_dir_name = 'repo_saporo'
    template_json_file = 'saporo.json.template'
    g_variable_names = ['SAPORO_IsBusy']

    @classmethod
    def cmd_create_vdev(cls,args):
        '''create new vdev on remote hc2 with saporo vdev templates'''
        t_json_root = os.path.join(os.path.dirname(os.path.abspath(__file__)),
            cls.repo_dir_name)
        
        # get template vdev json
        with open(os.path.join(t_json_root,cls.template_json_file)) as fh:
            t_vdev = json.loads(fh.read())
            
        # get hc2 service
        hc2 = cls.get_args_hc2(args)
        
        # create saporo vdev
        t_vdev = hc2.vdev_create(t_vdev)
        if t_vdev:
            sys.stderr.write('success to create saporo vdev (%s) on remote hc2\n' %
                             t_vdev['id'])
        else:
            sys.stderr.write('fail to create saporo vdev on remote hc2\n')
            return None
        
        # create saporo hc2 global variables SAPORO_IsBusy
        for var_name in cls.g_variable_names:
            t_var = hc2.gvar_query(var_name)
            if t_var:
                sys.stderr.write('global variable %s already exist, skip\n' % var_name)
            else:
                t_var = hc2.gvar_create(var_name,'')
                if t_var:
                    sys.stderr.write('success to create global variable %s\n%s\n' % (t_var,json.dumps(t_var,indent=2)))
                else:
                    sys.stderr.write('fail to create global variable %s\n' % t_var)
        
        return t_vdev
    
    @classmethod
    def get_cmd_parser(cls,base_parser,subparsers):
        cmd_parser = subparsers.add_parser(
            'saporo',
            description=__doc__,
            help='sapooro vdev command tool',
            parents=[base_parser])

        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')
        
        # create_vdev
        scmd_parser = scmd_subparsers.add_parser(
            'create_vdev',
            help=cls.cmd_create_vdev.__doc__,
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_create_vdev)        

        return cmd_parser
        
