

import sys

from cmd_base import CMDBase


class CMDTopology(CMDBase):

    # astr_category = 'category'

    @classmethod
    def cmd_pull(cls, args):
        # sys.stderr.write('pull remote {args.hostname} topology with category {args.category}\n'.format(
        #     args=args))
        hc2 = cls.get_args_hc2(args)
        topology_file = hc2.topology_pull()
        sys.stdout.write(topology_file)
        if topology_file:
            sys.stderr.write('success save remote({args.hostname}) topology file {topology_file}\n\n'.format(
                args=args, topology_file=topology_file))
        else:
            sys.stderr.write('fail to save remote({args.hostname}) topology file\n\n'.format(
                args=args))

    # @classmethod
    # def add_parser_arg_category(cls, parser):
    #     parser.add_argument(
    #         cls.astr_category,
    #         nargs='?',
    #         choices=['all', 'devices', 'scenes', 'rooms'],
    #         type=lambda c: c.lower(),
    #         help='hc2 category symbol, default:%(default)s',
    #         default='SCENES')

    @classmethod
    def get_cmd_parser(cls, base_parser, subparsers):
        cmd_parser = subparsers.add_parser(
            'topology',
            description=__doc__,
            help='hc2 topology command tool',
            parents=[base_parser])

        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')

        # topology pull <remote>
        scmd_parser = scmd_subparsers.add_parser(
            'pull',
            help='pull hc2 topology json and save as local file',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_pull)

        return cmd_parser
