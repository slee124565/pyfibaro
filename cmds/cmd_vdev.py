'''
Command Tool for HC2 Virtual Devices
'''

import sys

from cmd_dev import CMDDevice

class CMDVDevice(CMDDevice):
    
    @classmethod
    def cmd_clone(cls,args):
        '''create new vdev on remote hc2 with existing vdev with dev_id'''
        hc2 = cls.get_args_hc2(args)
        dev_id = getattr(args, cls.astr_dev_id)
        
        # dev_pull wiht dev_id
        src_dev = hc2.dev_pull(dev_id)
        
        # vdev_create with src_dev
        t_vdev = hc2.vdev_create(src_dev)
        
        # report result
        if t_vdev:
            sys.stderr.write('success to clone vdev (%s) from src vdev (%s) %s\n' %
                             (t_vdev['id'],dev_id,src_dev['name'].encode('utf8')))
        else:
            sys.stderr.write('fail to clone vdev from src vdev (%s) %s\n' %
                             (dev_id,src_dev['name'].encode('utf8')))
        
        return t_vdev
    
    @classmethod
    def cmd_push(cls,args):
        '''update vdev on  remote hc2 with local dumped files including buttons and mainLoop'''
        hc2 = cls.get_args_hc2(args)
        dev_id = getattr(args, cls.astr_dev_id)
         
        # rebuild vdev with local files and update remote hc2 
        t_vdev = hc2.vdev_update(dev_id)
        
        remote_name = getattr(args, cls.astr_remote_name,None)
        # report result
        if t_vdev:
            sys.stderr.write('success to update vdev (%s,%s) on remote hc2 (%s)\n' % (
                t_vdev['id'],t_vdev['name'].encode('utf8'),remote_name))
        else:
            sys.stderr.write('fail to update vdev (%s,%s) on remote hc2 (%s)\n' % (
                t_vdev['id'],t_vdev['name'].encode('utf8'),remote_name))

        return t_vdev
        
    @classmethod
    def cmd_delete(cls,args):
        '''delete remote hc2 virtual device'''
        hc2 = cls.get_args_hc2(args)
        dev_id = getattr(args, cls.astr_dev_id)
        hc2.vdev_delete(dev_id)
        sys.stderr.write('success to delete vdev id %s \n' % dev_id)
        
    @classmethod
    def get_cmd_parser(cls,base_parser,subparsers):
        cmd_parser = subparsers.add_parser(
            'vdev',
            description=__doc__,
            help='hc2 virtual device command tool',
            parents=[base_parser])
        
        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')
        
        # vdev pull <remote> <dev_id>
        scmd_parser = scmd_subparsers.add_parser(
            'pull',
            help='save remote hc2 device object json',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_dev_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_pull)
        
        # vdev push <remote> <dev_id>
        scmd_parser = scmd_subparsers.add_parser(
            'push',
            help=cls.cmd_push.__doc__,
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_dev_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_push)

        # vdev clone <remote> <dev_id>
        scmd_parser = scmd_subparsers.add_parser(
            'clone',
            help=cls.cmd_clone.__doc__,
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_dev_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_clone)

        # vdev delete <remote> <dev_id>
        scmd_parser = scmd_subparsers.add_parser(
            'delete',
            help=cls.cmd_delete.__doc__,
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_dev_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_delete)
        
        return cmd_parser
        
