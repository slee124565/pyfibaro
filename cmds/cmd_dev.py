'''
Command Tool for HC2 Devices
'''

import sys

from cmd_base import CMDBase
    
class CMDDevice(CMDBase):

    @classmethod
    def cmd_push(cls,args):
        '''todo not implement yet'''
         
        sys.stderr.write('ERROR: command push not implement yet')
        
    @classmethod
    def cmd_pull(cls,args):
        ''''''
        hc2 = cls.get_args_hc2(args)
        dev_id = getattr(args, cls.astr_dev_id)
        if hc2.dev_pull(dev_id):
            sys.stderr.write('success pull remote({args.hostname}) device(id:{args.dev_id})\n\n'.format(
                args=args))
        else:
            sys.stderr.write('fail to pull remote({args.hostname}) device(id:{args.dev_id})\n\n'.format(
                args=args))

    @classmethod
    def get_cmd_parser(cls,base_parser,subparsers):
        cmd_parser = subparsers.add_parser(
            'dev',
            description=__doc__,
            help='hc2 device command tool',
            parents=[base_parser])
        
        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')
        
        # dev pull <remote> <dev_id>
        scmd_parser = scmd_subparsers.add_parser(
            'pull',
            help='save hc2 device object json',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_dev_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_pull)
        
#         # dev push <remote> <dev_id>
#         scmd_parser = scmd_subparsers.add_parser(
#             'push',
#             help='update hc2 device object with json',
#             parents=[base_parser])
#         cls.add_parser_arg_remote_name(scmd_parser)
#         cls.add_parser_arg_dev_id(scmd_parser)
#         scmd_parser.set_defaults(func=cls.cmd_push)

        return cmd_parser
        
