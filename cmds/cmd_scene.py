"""
Command Tool for HC2 Scene
"""

import sys

from cmd_base import CMDBase


class CMDScene(CMDBase):

    @classmethod
    def cmd_start(cls,args):
        """start scene with scene_id on remote hc2"""

        hc2 = cls.get_args_hc2(args)
        scene_id = getattr(args, cls.astr_scene_id)
        if hc2.scene_start(scene_id):
            sys.stderr.write('success activate remote({args.hostname}) scene(id:{args.scene_id})\n\n'.format(
                args=args))
        else:
            sys.stderr.write('fail to activate remote({args.hostname}) scene(id:{args.scene_id})\n\n'.format(
                args=args))

    @classmethod
    def cmd_list(cls,args):
        """list all scene name from hc2"""

        hc2 = cls.get_args_hc2(args)
        hc2.scene_list()

    @classmethod
    def cmd_pull(cls,args):
        """dump scene lua code from remote hc2"""

        hc2 = cls.get_args_hc2(args)
        scene_id = getattr(args, cls.astr_scene_id)
        if hc2.scene_pull(scene_id):
            sys.stderr.write('success pull remote({args.hostname}) scene(id:{args.scene_id})\n\n'.format(
                args=args))
        else:
            sys.stderr.write('fail to pull remote({args.hostname}) scene(id:{args.scene_id})\n\n'.format(
                args=args))

    @classmethod
    def cmd_push(cls,args):
        """update scene on remote hc2 with local dumped files including lua file"""

        hc2 = cls.get_args_hc2(args)
        scene_id = getattr(args, cls.astr_scene_id)
         
        # rebuild vdev with local files and update remote hc2 
        scene = hc2.scene_update(scene_id)
        
        # report result
        if scene:
            sys.stderr.write('success to update scene (%s,%s) on remote hc2 (%s)\n' % (
                scene['id'],scene['name'],args.hostname))
        else:
            sys.stderr.write('fail to update scene (%s,%s) on remote hc2 (%s)\n' % (
                scene['id'],scene['name'],args.hostname))

        return scene

    @classmethod
    def get_cmd_parser(cls,base_parser,subparsers):
        cmd_parser = subparsers.add_parser(
            'scene',
            description=__doc__,
            help='hc2 scene command tool',
            parents=[base_parser])
        
        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')
        
        # scene pull <remote> <scene_id>
        scmd_parser = scmd_subparsers.add_parser(
            'pull',
            help='save hc2 scene object json',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_scene_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_pull)
        
        # scene push <remote> <scene_id>
        scmd_parser = scmd_subparsers.add_parser(
            'push',
            help='update hc2 scene object with json',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_scene_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_push)

        # scene list <remote>
        scmd_parser = scmd_subparsers.add_parser(
            'list',
            help='list hc2 scene name and id',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_list)

        # scene start <remote> <scene_id>
        scmd_parser = scmd_subparsers.add_parser(
            'start',
            help='start hc2 scene with scene_id',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_scene_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_start)

        return cmd_parser
