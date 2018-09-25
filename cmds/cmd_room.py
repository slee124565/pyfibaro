"""
Command Tool for HC2 Rooms
"""

import sys

from cmd_base import CMDBase


class CMDRoom(CMDBase):

    @classmethod
    def cmd_list(cls, args):
        """list all room from hc2"""

        hc2 = cls.get_args_hc2(args)
        hc2.room_list()

    @classmethod
    def get_cmd_parser(cls, base_parser, subparsers):
        cmd_parser = subparsers.add_parser(
            'room',
            description=__doc__,
            help='hc2 room command tool',
            parents=[base_parser])

        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')

        # room list <remote>
        scmd_parser = scmd_subparsers.add_parser(
            'list',
            help='list hc2 room name and id',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_list)

        return cmd_parser
