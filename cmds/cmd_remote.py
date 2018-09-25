"""
Command Tool for Local Variables Config
"""

import sys
import json
from cmd_base import CMDBase
from remotes import RemoteCollection


class CMDRemote(CMDBase):
    """"""
    
    @classmethod
    def cmd_add(cls, args):
        """add remote hc2 network settings into local json config file"""
        
        name = getattr(args, cls.astr_remote_name, None)
        t_remote = {
            cls.astr_hostname: getattr(args, cls.astr_hostname,None),
            cls.astr_hostport: getattr(args, cls.astr_hostport,None),
            cls.astr_username: getattr(args, cls.astr_username,None),
            cls.astr_password: getattr(args, cls.astr_password,None),
        }
        t_remotes = RemoteCollection(args)
        t_remotes[name] = t_remote
        t_remotes._save_config_file()
        t_remotes.logger.debug('%s' % t_remotes.remotes.keys())
        sys.stderr.write('remote (%s) added\n\n' % name)

    @classmethod
    def cmd_rm(cls, args):
        """remove hc2 config from local json config file"""
        name = getattr(args, cls.astr_remote_name, None)
        t_remotes = RemoteCollection(args)
        del t_remotes[name]
        sys.stderr.write('remote (%s) removed\n\n' % name)

    @classmethod
    def cmd_list(cls, args):
        """list all remote hc2 name text in local json config file"""
        t_remotes = RemoteCollection(args)
        if len(t_remotes.remotes.keys()) > 0:
            sys.stderr.write('remotes:\n')
            count = 1
            for name in t_remotes.remotes.keys():
                sys.stderr.write('{count} {name}: ({remote})\n'.format(
                    count=count, name=name, remote=str(t_remotes[name])))
                count += 1
        else:
            sys.stderr.write('no remotes exist\n')
        sys.stderr.write('\n')

    @classmethod
    def cmd_get(cls, args):
        """get remote hc2 settings in local json config file"""
        remote_name = getattr(args, cls.astr_remote_name, None)
        t_remotes = RemoteCollection(args)
        t_remote = t_remotes.remotes.get(remote_name, None)
        if t_remote:
            sys.stdout.write('{}\n'.format(json.dumps(t_remote, indent=2)))
            # return json.dumps(t_remote, indent=2)
        # else:
        #     import os
        #     sys.stdout.write('{}\n'.format(os.getcwd()))


    # @classmethod
    # def cmd_topology_update(cls, args):
    #     """create topology json (rooms, scenes, devices, ...) file for remote hc2"""
    #     hc2 = cls.get_args_hc2(args)
    #     topology_file = hc2.remote_topology_update()
    #     if topology_file:
    #         sys.stderr.write('success save remote({args.hostname}) topology file {topology_file}\n\n'.format(
    #             args=args, topology_file=topology_file))
    #     else:
    #         sys.stderr.write('fail to save remote({args.hostname}) topology file\n\n'.format(
    #             args=args))
    #
    @classmethod
    def get_cmd_parser(cls, base_parser, subparsers):
        cmd_parser = subparsers.add_parser(
            'remote',
            description=__doc__,
            help='config remote hc2 network settings',
            parents=[base_parser])
        
        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')
        
        # remote add
        scmd_parser = scmd_subparsers.add_parser(
            'add',
            help='add remote hc2 network settings',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_hostname(scmd_parser)
        cls.add_parser_arg_hostport(scmd_parser)
        cls.add_parser_arg_username(scmd_parser)
        cls.add_parser_arg_password(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_add)
        
        # remote rm
        scmd_parser = scmd_subparsers.add_parser(
            'rm',
            help='delete remote hc2 networking settings from config',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_rm)

        # remote list
        scmd_parser = scmd_subparsers.add_parser(
            'list',
            help='list existing remote name',
            parents=[base_parser])
        scmd_parser.set_defaults(func=cls.cmd_list)

        # remote get
        scmd_parser = scmd_subparsers.add_parser(
            'get',
            help='get remote hc2 network settings from config',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_get)

        # # remote topology update
        # scmd_parser = scmd_subparsers.add_parser(
        #     'updatetopology',
        #     help='update local topology json file with remote hc2',
        #     parents=[base_parser])
        # cls.add_parser_arg_remote_name(scmd_parser)
        # scmd_parser.set_defaults(func=cls.cmd_topology_update)
        #
        return cmd_parser
