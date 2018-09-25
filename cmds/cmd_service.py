"""
Command Tool for HC2 Service
"""

import sys

from cmd_base import CMDBase


class CMDService(CMDBase):

    @classmethod
    def cmd_reboot(cls, args):
        """reboot hc2 service"""

        hc2 = cls.get_args_hc2(args)

        return hc2.service_reboot()

    @classmethod
    def get_cmd_parser(cls, base_parser, subparsers):
        cmd_parser = subparsers.add_parser(
            'service',
            description=__doc__,
            help='hc2 service command tool',
            parents=[base_parser])

        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')

        # service reboot <remote>
        scmd_parser = scmd_subparsers.add_parser(
            'reboot',
            help='reboot hc2 service',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_reboot)
