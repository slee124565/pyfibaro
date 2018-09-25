#!/usr/bin/env python
"""
HC2CliService class module implement the functions which hc2cli commmand tool needed
"""

import logging
logger = logging.getLogger(__name__)


class HC2CliService(object):

    def __init__(self, args=None, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.args = args

    # -- common functions
    @staticmethod
    def _list_name_id(host_name, api_name, data_set):

        count = 1
        import sys
        if data_set:
            sys.stderr.write('remote hc2 (%s) scene list (%s):\n' % (
                host_name, len(data_set)))
            for entry in data_set:
                sys.stderr.write('{count}: {name} (id: {scene_id})\n'.format(
                    count=count, name=entry['name'].encode('utf8'), scene_id=entry.get('id', None)))
                count += 1
        else:
            sys.stderr.write('err: no {api_name} available\n'.format(api_name=api_name))

    # -- functions for command [dev]
    def dev_pull(self,dev_id):
        """query dev json from hc2 and save as local files including buttons and mainLoop code"""
        from hc2.base_service import HC2BaseService
        hc2 = HC2BaseService(self.args, self.logger)
        device = hc2.dump_device(dev_id)
        return device
    
    # -- functions for command [vdev]
    def vdev_delete(self,dev_id):
        """delete hc2 vdev with http delete method"""        
        from hc2.api_vdev import HC2APIVirtualDevice
        hc2 = HC2APIVirtualDevice(self.args, self.logger)
        result = hc2.delete(dev_id)
        return result
    
    def vdev_create(self,dev):
        """create hc2 vdev with http post method"""        
        from hc2.api_vdev import HC2APIVirtualDevice
        hc2 = HC2APIVirtualDevice(self.args, self.logger)
        device = hc2.post(dev)
        if device:
            # when create new vdev, it needs to post origin dev object in order to update dev btn and mainloop
            dev['id'] = device['id']
            device = hc2.put(dev['id'], dev)
        return device
    
    def vdev_update(self,dev_id):
        """rebuild vdev with local dumped files (json, btn, mainLoop) and 
        update hc2 vdev with http put method"""
        from hc2.base_service import HC2BaseService
        hc2 = HC2BaseService(self.args, self.logger)
        return hc2.update_vdevice(dev_id)
    
    # -- functions for command [gvar]
    def gvar_query(self,var_name):
        """query hc2 global variable with http get method"""
        from hc2.api_gvar import HC2APIGlobalVariable
        hc2 = HC2APIGlobalVariable(self.args, self.logger)
        var = hc2.get(var_name)
        return var
    
    def gvar_create(self,var):
        """create hc2 global variable with http post method"""
        from hc2.api_gvar import HC2APIGlobalVariable
        hc2 = HC2APIGlobalVariable(self.args, self.logger)
        t_var = hc2.post(var)
        return t_var
    
    def gvar_delete(self,var_name):
        """delete hc2 global variable with http delete method"""
        from hc2.api_gvar import HC2APIGlobalVariable
        hc2 = HC2APIGlobalVariable(self.args, self.logger)
        var = hc2.delete(var_name)
        return var
    
    def gvar_update(self,var_name,var):
        """update hc2 global variable value with http put mthod"""
        from hc2.api_gvar import HC2APIGlobalVariable
        hc2 = HC2APIGlobalVariable(self.args, self.logger)
        t_var = hc2.put(var_name,var)
        return t_var
    
    def gvar_pull(self,var_name):
        """query and save hc2 global variable on local file"""
        from hc2.base_service import HC2BaseService
        hc2 = HC2BaseService(self.args, self.logger)
        gvar = hc2.pull_gvar(var_name)
        return gvar
    
    def gvar_push(self,var_name):
        """update hc2 global variable value with local file"""
        from hc2.base_service import HC2BaseService
        hc2 = HC2BaseService(self.args, self.logger)
        gvar = hc2.push_gvar(var_name)
        return gvar
    
    def gvar_list(self):
        """list all global variable name from remote hc2"""
        from hc2.api_gvar import HC2APIGlobalVariable
        hc2 = HC2APIGlobalVariable(self.args, self.logger)
        g_vars = hc2.get('')
        self._list_name_id(host_name=hc2.hostname,
                           api_name='globalVariables',
                           data_set=g_vars)

    # -- functions for command [scene]
    def scene_pull(self, scene_id):
        """query and save scene json from hc2 and save as local files including buttons and mainLoop code"""

        from hc2.scene_service import HC2SceneService
        hc2 = HC2SceneService(self.args, self.logger)
        scene = hc2.dump_scene(scene_id)
        return scene
    
    def scene_update(self, scene_id):
        """rebuild scene with local dumped files (json,lua) and 
        update hc2 scene with http put method"""

        from hc2.scene_service import HC2SceneService
        hc2 = HC2SceneService(self.args, self.logger)
        return hc2.update_scene(scene_id)

    def scene_list(self):
        """list current scene name & id on remote hc2"""

        from hc2.scene_service import HC2SceneService
        hc2 = HC2SceneService(self.args, self.logger)
        scenes = hc2.get_scenes()
        self._list_name_id(host_name=hc2.hostname,
                           api_name='scenes',
                           data_set=scenes)

    def scene_start(self, scene_id):
        """start hc2 scene with scene_id"""

        from hc2.scene_service import HC2SceneService
        hc2 = HC2SceneService(self.args, self.logger)
        return hc2.start_scene(scene_id)

    # -- function for command [service]
    def service_reboot(self):
        """reboot hc2"""
        from hc2.api_service import HC2APIService
        hc2 = HC2APIService(self.args, self.logger)
        data = hc2.reboot()
        import sys
        sys.stderr.write('remote hc2 (%s) service reboot return data %s\n' % (hc2.hostname, data))

    # -- function for command [rooms]
    def room_list(self):
        """list current room on remote hc2"""
        from hc2.room_service import HC2RoomService
        hc2 = HC2RoomService(self.args, self.logger)
        rooms = hc2.get_rooms()
        self._list_name_id(host_name=hc2.hostname,
                           api_name='rooms',
                           data_set=rooms)

    # -- functions for command [topology]
    def topology_pull(self, category='all'):
        """pull hc2 topology with category [all, devices, scenes, rooms]"""
        from hc2.base_service import HC2BaseService
        hc2 = HC2BaseService(self.args, self.logger)
        return hc2.update_hc2_topology_file()

    def topology_get(self):
        from hc2.base_service import HC2BaseService
        hc2 = HC2BaseService(self.args, self.logger)
        return hc2._get_hc2_topology_file()

    # def remote_topology_create(self):
    #     """create topology json (rooms, scenes, devices, ...) file for remote hc2"""
    #     from hc2.base_service import HC2BaseService
    #     hc2 = HC2BaseService(self.args, self.logger)
    #     return hc2.save_hc2_topology()
    #
    # def remote_topology_update(self):
    #     """create topology json (rooms, scenes, devices, ...) file for remote hc2"""
    #     from hc2.base_service import HC2BaseService
    #     hc2 = HC2BaseService(self.args, self.logger)
    #     return hc2.update_hc2_topology_file()

    # -- functions for command [daikin]
    def daikin_create_vdev(self,dev):
        """create hc2 daikin vdev with vdev_create command"""
        t_dev = self.vdev_create(dev)
        return t_dev    
    
    def daikin_parse_btn_cmd_arg(self, dev_id):
        """"""
        from hc2.base_service import HC2BaseService
        hc2 = HC2BaseService(self.args, self.logger)
        cmd_arg_list = hc2.backup_vdev_btn_cmd_arg(dev_id)
        return cmd_arg_list
    
    def daikin_btn_cmd_arg_file_path(self, dev_id):
        from hc2.base_service import HC2BaseService
        hc2 = HC2BaseService(self.args, self.logger)
        return hc2.get_vdev_btn_cmd_arg_file_path(dev_id)
    
    def daikin_update_btn_cmd_arg(self, dev_id):
        from hc2.base_service import HC2BaseService
        hc2 = HC2BaseService(self.args, self.logger)
        cmd_arg_list = hc2.restore_btn_cmd_arg_value(dev_id)
        return cmd_arg_list
    
    def daikin_btn_cmd_arg_file_code_update(self, dev_id):
        cmd_arg_file_path = self.daikin_btn_cmd_arg_file_path(dev_id)
        from cmds.repo_daikin.daikin_btn_cmd_tool import daikin_cmd_arg_code_update
        daikin_cmd_arg_code_update(cmd_arg_file_path)


if __name__ == '__main__':

    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='a python utility to execute function by cmd arg')

    parser.add_argument(
        'username',
        help='hc2 username for login'
    )

    parser.add_argument(
        'password',
        help='hc2 password for login'
    )

    parser.add_argument(
        'hostname',
        help='hc2 hostname or IP for login'
    )

    parser.add_argument(
        'hostport',
        help='hc2 web api port for access'
    )

    parser.add_argument(
        'command',
        help='function name as command to be executed'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='print debug message',
        default=False
    )

    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    if args.debug:
        logger.setLevel(logging.DEBUG)

    cmd = HC2CliService(args=args, logger=logger)

    try:
        logger.debug('{} cmd tool with args: {}'.format(cmd.__class__.__name__, args))
        cmd_func = getattr(cmd, args.command)
        cmd_result = cmd_func()
        logger.debug('execute {} function {} with result:\n{}'.format(
            cmd.__class__.__name__, args.command, cmd_result))
        if cmd_result:
            sys.stdout.write('{}'.format(cmd_result))
    except:
        logger.error('{} cmd tool exception'.format(cmd.__class__.__name__), exc_info=True )
