#!/usr/bin/env python
"""

This module is an utility and class library to interact with Fibaro HC2 system via internet.

Note:: change the constant variables (HC2_IP,HC2_USERNAME,HC2_PASSWORD) before using it.

Utility Tool Usage Examples:

    * Virtual Device Backup and Restore *

        - save hc2 device json as local files (create code files in mainloop and buttons as seperate).
            $ python api.py dump_device,<dev_id>
        
        - update hc2 VIRTUAL device with local dump files (including mainloop and buttons code files).
            $ python api.py update_vdevice,<dev_id>
        
        - clone hc2 VIRTUAL device with local dump files (including mainloop and buttons code files).
            $ python api.py clone_vdevice,<dev_id>

    * Virtual Device Button Config *

        - update hc2 VIRTUAL device buttons settings (lua,waitForResponse)
            $ python api.py set_vdevice_btns,<dev_id>,<lua=0|1><wait=0|1>
       
    * Virtual Device Button <cmdText> <argText> Backup and Restore*

        - clone hc2 VIRTUAL device buttons code update from local
            $ python api.py clone_vdev_btn,<dev_id>,<src_btn_id>,<dest_btn_id>

        - backup hc2 VIRTUAL device buttons <cmdText><argText> to local backup file
            $ python api.py backup_vdev_btn_cmd_arg,<dev_id>
       
        - restore local btn_cmd_arg file value for local btn dump file content (cmdText = <value> and argText = <value>)
            $ python api.py restore_btn_cmd_arg_value,<local_dev_id>
   
"""

from api_scene import HC2APIScene
from api_gvar import HC2APIGlobalVariable

import logging
import re
import os
import json
import shutil
import fnmatch
import fileinput
import csv
import sys
import codecs

CMD_MATCH_STR = 'local cmdText ='
ARG_MATCH_STR = 'local argText ='


class HC2BaseService(object):

    astr_username = 'username'
    astr_password = 'password'
    astr_hostname = 'hostname'
    astr_hostport = 'hostport'

    username = None
    password = None
    hostname = None
    hostport = None
    args = None

    def __init__(self, args=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.username = getattr(args, self.astr_username, None)
        self.password = getattr(args, self.astr_password, None)
        self.hostname = getattr(args, self.astr_hostname, None)
        self.hostport = getattr(args, self.astr_hostport, 80)
        self.api_root = 'http://%s:%s/api' % (self.hostname,self.hostport)
        self.args = args
        
        if self.username is None or self.password is None and self.hostname is None:
            raise ValueError('%s init with error username or password or hostname' %
                             self.__class__.__name__)
    
    def __str__(self, *args, **kwargs):
        return '%s (%s:%s)' % (self.__class__.__name__,self.hostname,self.hostport)
    
    # __getitem__ implement start
    def __getitem__(self,key):
        """key: [obj_group]-[obj_id]"""
        
        params = re.split(',|\s|-|\.',key)
        self.logger.debug('__getitem__ key parse as %s' % str(params))
        obj_group = params[0]
        obj_id = None
        if len(params) > 1:
            obj_id = params[1]
            
        func_name = '_get_%s' % obj_group
        func = getattr(self,func_name,None)
        self.logger.debug('__getitem__ call %s with obj id %s' % (func_name,obj_id))

        if func:
            hc2_group = func()
            if obj_id:
                for obj in hc2_group:
                    if str(obj['id']) == obj_id:
                        return obj
                self.logger.warning('__getitem__ group %s has no id %s' % (obj_group,obj_id))
                return None
            else:
                return hc2_group
        else:
            self.logger.warning('item %s not exist in %s' % (key,
                                                             self.__class__.__name__))
            return None
        
    def _get_devices(self):
        """return hc2 /api/devices"""
        import api_dev
        hc2_dev_api = api_dev.HC2APIDevice(self.args,self.logger)
        t_devices = hc2_dev_api.get(key=None)
        if t_devices:
            self._devices = t_devices
        else:
            self.logger.warning('hc2 device api for all devices call fail')
           
        return t_devices 
        
    def _get_device_by_id(self,dev_id):
        return self['devices.'+str(dev_id)]
        
    # def _get_scenes(self):
    #     """return hc2 /api/scenes"""
    #
    #     import api_scene
    #     hc2_scene_api = api_scene.HC2APIScene(self.args, self.logger)
    #     t_scenes = hc2_scene_api.get(key=None)
    #     if t_scenes:
    #         self._scenes = t_scenes
    #     else:
    #         self.logger.warning('hc2 scenes api for all scenes call fail')
    #
    #     raise t_scenes
    #
    def _get_variables(self):
        """return hc2 /api/globalVariables"""

        import api_gvar
        hc2_gvar_api = api_gvar.HC2APIGlobalVariable(self.args, self.logger)
        t_gvars = hc2_gvar_api.get(key=None)
        if t_gvars:
            self._gvars = t_gvars
        else:
            self.logger.warning('hc2 globalVariables api for all variables call fail')

        raise t_gvars

    # __getitem__ implement end
    
    # --- dump_device
    def _get_dump_root(self, del_exist=False):
        dump_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), '.dump', self.hostname)

        if os.path.exists(dump_path):
            if del_exist:
                shutil.rmtree(dump_path)
                os.makedirs(dump_path)
        else:
            os.makedirs(dump_path)
        return dump_path
    
    # def _get_scene_dump_path(self,scene_id,del_exist=False):
    #     """ create dump folder (./.dump/hostname/scenes/scene_id) if not exist"""
    #     dump_path = os.path.join(
    #         self._get_dump_root(),'scenes',str(scene_id))
    #     if os.path.exists(dump_path):
    #         if del_exist:
    #             shutil.rmtree(dump_path)
    #             os.makedirs(dump_path)
    #     else:
    #         os.makedirs(dump_path)
    #     return dump_path
    #
    def _get_dev_dump_path(self,dev_id,del_exist=False):
        """ create dump folder (./.dump/hostname/devices/dev_id) if not exist"""
        dump_path = os.path.join(
            self._get_dump_root(),'devices',str(dev_id))
        if os.path.exists(dump_path):
            if del_exist:
                shutil.rmtree(dump_path)
                os.makedirs(dump_path)
        else:
            os.makedirs(dump_path)
        return dump_path
    
    def _get_dev_json_dump_filename(self,dev):
        """{dev_id}.{dev_name}.json"""
        dev_name = dev['name']
        if dev_name.find('/') >= 0:
            self.logger.warning('device name %s is invalid filename, replace it with underline(_)' % 
                                dev_name.decode('unicode-escape').encode('utf8'))
            dev_name = dev_name.replace('/','_')
        filename = '{dev_id}.{dev_name}.json'.format(
            dev_id=dev['id'],
            dev_name=dev_name.encode('utf8')) 
        #filename = '{dev_id}.json'.format(dev_id=dev['id'])
        return filename.decode('utf8')
        
    def _get_dev_btn_dump_filename_by_btn_id(self,dev,btn_id):
        """{dev_id}.button.{id}.{name}.{caption}.lua if it is lua button
        {dev_id}.button.{id}.{name}.{caption}.txt if is is sck text button
        """
        self.logger.debug('... _get_dev_btn_dump_filename_by_btn_id(dev=%s,btn_id=%s)' % (
            dev['name'].encode('utf8'),btn_id))
        buttons = self._get_dev_all_buttons(dev)
        for button in buttons:
            if str(button['id']) == str(btn_id): 
                filename = self._get_dev_btn_dump_filename(dev['id'], button)
                self.logger.debug('... btn_dump_filename %s' % 
                                  filename.encode('utf8'))
                return filename
        self.logger.warning('... can not find button dump filename!')
        return None
        
    def _get_dev_btn_dump_filename(self,dev_id,button):
        """{dev_id}.button.{id}.{name}.{caption}.lua if it is lua button
        {dev_id}.button.{id}.{name}.{caption}.txt if is is sck text button
        """
        btn_id = button['id']
        btn_name = button['name']
        btn_caption = button['caption']
        if btn_caption.find('/') >= 0:
            self.logger.warning('btn caption %s is invalid filename, replace it with underline(_)' %
                                btn_caption.decode('unicode-escape').encode('utf8'))
            btn_caption = btn_caption.replace('/','_')
        filename = '{dev_id}.button.{id}.{name}.{caption}'.format(
            dev_id=dev_id,
            id=btn_id,
            name=btn_name,
            caption=btn_caption.encode('utf8'))
        if button['lua']:
            filename += '.lua'
        else:
            filename += '.txt'
        return filename.decode('utf8')
    
    def _get_dev_mainloop_dump_filename(self,dev):
        """{dev_id}.main.{dev_name}.lua"""
        filename = '{dev_id}.main.{dev_name}.lua'.format(
            dev_id=dev['id'],dev_name=dev['name'].encode('utf8'))
        return filename.decode('utf8')

    def _dump_device(self,dump_path,device):
        """save hc2 device json file ({dev_id}.{dev_name}.json) 
        and msg of button element content:
            lua: button.{id}.{name}.{caption}.lua
            sck: button.{id}.{name}.{caption}.txt
        and mainloop code:
            main.{dev_name}.lua
        """

        # dump json
        filename = self._get_dev_json_dump_filename(device)
        #with open(os.path.join(dump_path,filename),'w') as fh:
        with codecs.open(os.path.join(dump_path,filename), 'wb', encoding='utf8') as fh: 
            fh.write(json.dumps(device,indent=2))
        self.logger.debug('device %s (%s) json dumped' % (device['id'], device['name']))
        
        buttons = []
        if device['properties'].get('rows'):
            for entry in device['properties']['rows']:
                if entry['type'] == 'button':
                    buttons += entry['elements']
            
        # dump buttons
        if len(buttons) > 0:
            for button in buttons:
                btn_msg = button['msg']
                btn_msg = btn_msg.encode('utf-8').replace('\\n','\n')
                btn_caption = button['caption']
                filename = self._get_dev_btn_dump_filename(device['id'],button)
                #with open(os.path.join(dump_path,filename),'wb') as fh:
                with codecs.open(os.path.join(dump_path,filename), 'wb', encoding='utf8') as fh: 
                    fh.write(btn_msg.decode('utf8'))
                self.logger.debug('dev btn %s msg dumped' % btn_caption)    

        # dump main loop
        if device['properties'].get('mainLoop'):
            mainloop = device['properties']['mainLoop']
            mainloop = mainloop.encode('utf-8').replace('\\n','\n')
            filename = self._get_dev_mainloop_dump_filename(device)
            with codecs.open(os.path.join(dump_path,filename), 'wb', encoding='utf8') as fh:
                fh.write(mainloop.decode('utf8'))
            self.logger.debug('dev mainloop code dumped %s' % filename)
            

    def dump_device(self,dev_id):
        """get hc2 device json object via HTTP API and save as local files"""
        
        self.logger.debug('dump_device %s' % dev_id)
         
        device = self._get_device_by_id(dev_id)
        if device:
            dump_path = self._get_dev_dump_path(dev_id,True)
            self._dump_device(dump_path, device)
            self.logger.debug('... dump_device [%s] completed' % device['name'])
            self.logger.debug('... dump path %s' % dump_path)
        else:
            self.logger.warning('dump_device with id %s result None')
            
        return device
            
    # --- update_vdevice
    def _get_dev_bak_path(self,dev_id,del_exist=False):
        """ create backup folder (./.dump/hostname/devices/dev_id.origin) if not exist"""
#         bak_path = os.path.join(
#             os.path.dirname(os.path.abspath(__file__)),'.dump',
        bak_path = os.path.join(self._get_dev_dump_path(dev_id),'%s.origin' % str(dev_id))
        
        if os.path.exists(bak_path):
            if del_exist:
                shutil.rmtree(bak_path)
        else:
            os.makedirs(bak_path)
        return bak_path
        
    def _button_update_with_dump_file(self,button,dev_id):
        # check device dump file exist
        dump_path = self._get_dev_dump_path(dev_id)
        btn_filename = self._get_dev_btn_dump_filename(dev_id,button)
        btn_file_path = os.path.join(dump_path,btn_filename)
        if not os.path.exists(btn_file_path):
            self.logger.warning('device button dump file %s not exist' % btn_file_path)
            return
        
        # update hc2 device button msg content via hc2 api
        with open(btn_file_path) as fh:
            btn_msg = fh.read()
            btn_msg.replace('\n','\\n')
            self.logger.debug('... new msg content: %s' % btn_msg)
            
        # update device rows poperties
        button['msg'] = btn_msg
        self.logger.debug('... button [%s] msg changed' % button['caption'])
            
    def _get_vdev_by_id(self,dev_id,backup=False):

        # check dev_id exist in hc2
        dev = self._get_device_by_id(dev_id)
        if dev is None:
            self.logger.warning('device id %s is invalid' % dev_id)
            return None
        
        # check dev is virtual
        if dev['type'] != 'virtual_device':
            self.logger.warning('device id %s is not a virtual device' % dev_id)
            return None
        
        # backup origin dev json
        if backup:
            backup_path = self._get_dev_bak_path(dev_id)
            self._dump_device(dump_path=backup_path,device=dev)
        
        return dev
    
    def _get_dev_all_buttons(self,dev):
        buttons = []
        for entry in dev['properties']['rows']:
            entry_type = entry['type']
            for element in entry['elements']:
                if entry_type == 'button':
                    buttons.append(element)
        return buttons
        
    def _update_vdev_on_hc2(self,dev):

        import api_vdev
        hc2_vdev_api = api_vdev.HC2APIVirtualDevice(self.args,self.logger)
        dev = hc2_vdev_api.put(dev['id'],dev)
        
        if dev:
            self.logger.debug('hc2 virtual device (%s:%s) update completed' % (
                dev['id'],dev['name'].encode('utf8')))
        else:
            self.logger.warning('hc2 virtual device (%s:%s) put api fail' % (
                dev['id'],dev['name'].encode('utf8')))
        return dev
            
    def update_vdevice(self,dev_id):
        """update hc2 virtual device with local dumped files
        and the origin virtual device json object will be backup"""

        self.logger.debug('update_vdevice %s with local dump files' % dev_id)
        # check vdev exist in hc2
        dev = self._get_vdev_by_id(dev_id)
        if dev is None:
            self.logger.warning('fail to get dev json from hc2, exit')
            return

        # load local dev json
        dump_path = self._get_dev_dump_path(dev_id)
        filename = self._get_dev_json_dump_filename(dev)
        if os.path.exists(os.path.join(dump_path,filename)) == False:
            self.logger.warning('vdevice id %s dump file (%s) not exist' % (dev_id,filename))
        with open(os.path.join(dump_path,filename)) as fh:
            t_dev = json.loads(fh.read())
            
        # update dev properties attr. ui.*
        for key in t_dev['properties']:
            if key.find('ui.') == 0:
                if dev['properties'].get(key,False):
                    if dev['properties'][key] != t_dev['properties'][key]:
                        dev['properties'][key] = t_dev['properties'][key]
                        self.logger.debug('... properties %s value %s updated' % (
                            key,t_dev['properties'][key]))

        # update dev properties attr. ip, and port
        for key in ['port','ip']:
            if dev['properties'][key] != t_dev['properties'][key]:
                dev['properties'][key] = t_dev['properties'][key]
                self.logger.debug('... properties %s value %s updated' % (
                    key,t_dev['properties'][key]))
            
        # update dev properties attr. mainLoop
        filename = self._get_dev_mainloop_dump_filename(dev)
        file_path = os.path.join(dump_path,filename)
        if os.path.exists(file_path):
            with open(file_path) as fh:
                mainloop = fh.read()
                #mainloop = mainloop.replace('\n','\\n')
                dev['properties']['mainLoop'] = mainloop
                self.logger.debug('... properties mainLoop updated')
        else:
            self.logger.warning('vdevice %s mainloop dump file (%s) not exist' % (
                dev_id,file_path))
        
        # update dev properties attr. rows button elements
        buttons = self._get_dev_all_buttons(dev)
        for button in buttons:
            self.logger.debug('... select button id %s with caption [%s]' % (
                button['id'],button['caption'].encode('utf8')))
        
        # update buttons msg
        for button in buttons:
            self._button_update_with_dump_file(button,dev_id)
        self.logger.debug('... properties row element buttons updated')
        
        # update dev attr. name
        if dev['name'] != t_dev['name']:
            dev['name'] = t_dev['name']
            self.logger.debug('... update vdev name as %s' % (
                dev['name'].encode('utf8')))
        
        # update vdev on hc2 vdevice
        vdev = self._update_vdev_on_hc2(dev)      
        
        self.logger.debug('... update_vdevice completed')
        
        return vdev
            
    # --- set vdev button attr lua, waitForResponse
    def set_vdevice_btns(self,dev_id,set_lua=False,set_wait=False):
        """update hc2 virtual device all buttons lua and waitForResponse attr."""
        
        self.logger.debug('set_vdevice_btns %s with lua: %s and waitForResponse: %s' % (
            dev_id,set_lua,set_wait))
        # check virtual device exist in hc2
        dev = self._get_vdev_by_id(dev_id)
        if dev is None:
            self.logger.warning('fail to get dev json from hc2, exit')
            return
        
        # collect all button elements
        buttons = self._get_dev_all_buttons(dev)
        
        # buttons config with func args
        for button in buttons:
            button['lua'] = True if int(set_lua) else False
            button['waitForResponse'] = True if int(set_wait) else False 
            
        # update vdev on hc2
        new_dev = self._update_vdev_on_hc2(dev)
        self.logger.debug('... hc2 virtual device updated')
        
        # save new vdev from hc2
        dump_path = self._get_dev_dump_path(dev_id, del_exist=True)
        self._dump_device(dump_path, new_dev)
        
        self.logger.debug('... set_vdevice_btns completed')
        
    # --- post vdev
    def clone_vdevice(self,local_dev_id):
        """create a new hc2 virtual device with local existing vdev json dumped file"""
        
        self.logger.debug('clone_vdevice with local dumped dev id %s' % local_dev_id)
        dump_path = self._get_dev_dump_path(local_dev_id)
        
        # serach *.json
        result = []
        for root, _, files in os.walk(dump_path):
            for name in files:
                if fnmatch.fnmatch(name, '*.json'):
                    result.append(os.path.join(root, name))
        if len(result) == 1:
            filename = result[0]
        else:
            self.logger.warning('there are multiple or none dev json files exist in dump path (%s)' %
                                dump_path)
            return None
        with open(filename) as fh:
            src_dev = json.loads(fh.read())
        
        # keep dev json keys ['name','type','actions','properties'] member only
        t_dev = dict(src_dev) # keep original dev json obj
        for key in t_dev.keys():
            if not key in ['name','type','actions','properties']:
                t_dev.pop(key,None)
        self.logger.debug('... dev json remain keys: %s' % t_dev.keys())
        
        # call hc2 post api to create vdev
        import api_vdev
        hc2_vdev_api = api_vdev.HC2APIVirtualDevice(self.args,self.logger)
        new_dev = hc2_vdev_api.post(t_dev)
        if new_dev:
            self.logger.debug('... new added vdev id is %s' % new_dev['id'])

            # update new_dev content with base_dev
            t_dev['id'] = new_dev['id']
            new_dev = self._update_vdev_on_hc2(t_dev)
            
            self.logger.debug('... clone_vdevice completed')
        else:
            self.logger.warning('hc2 virtual device (%s:%s) post api fail, status code %s' % (
                src_dev['id'],src_dev['name'].encode('utf8')))
                    
        return new_dev   
    
    def clone_vdev_btn(self,dev_id,src_btn_id,dest_btn_id=None):
        """clone hc2 VIRTUAL device all buttons code from one of its existing button
            $ python api.py clone_vdev_btn,<dev_id>,<src_btn_id>,<dest_btn_id>
        """
        
        self.logger.debug('clone_vdev_btn with dev_id %s, src_btn_id %s,dest_btn_id %s' % (
            dev_id,src_btn_id,dest_btn_id))
        
        # dump vdev from hc2
        dev = self.dump_device(dev_id)
        
        # get src btn dump filename
        src_btn_filename = self._get_dev_btn_dump_filename_by_btn_id(dev,src_btn_id)
        self.logger.debug('... src btn filename %s' % src_btn_filename)
        if src_btn_filename is None:
            self.logger.warning('can not clone vdev button code, exit')
            return None

        # get src btn dump filename
        dump_path = self._get_dev_dump_path(dev_id)
        src_btn_file_path = os.path.join(dump_path,src_btn_filename)
        #with open(src_btn_file_path) as fh:
        #    btn_msg = fh.read().encode('utf8')

        # cp src btn dump file to dest btn dump file
        buttons = self._get_dev_all_buttons(dev)
        for button in buttons:
            dest_btn_filename = self._get_dev_btn_dump_filename_by_btn_id(dev, button['id'])
            dest_btn_file_path = os.path.join(dump_path,dest_btn_filename)
            if dest_btn_id is None:
                # update all buttons
                t_btn_id = button['id']
                if str(t_btn_id) != str(src_btn_id):
                    shutil.copyfile(src_btn_file_path, dest_btn_file_path)
                    self.logger.debug('... cp src btn (%s) dump file for all btn (%s) dump file' % (
                        src_btn_id,t_btn_id))
                else:
                    self.logger.debug('... skip cp src btn (%s) dump file for all btn (%s) dump file' % (
                        src_btn_id,t_btn_id))
            else:
                if str(dest_btn_id) == str(button['id']):
                    shutil.copyfile(src_btn_file_path, dest_btn_file_path)
                    self.logger.debug('... cp src btn (%s) dump file for dest btn (%s) dump file' % (
                        src_btn_id,dest_btn_id))
                else:
                    self.logger.debug('... skip cp src btn (%s) dump file for dest btn (%s) dump file' % (
                        src_btn_id,dest_btn_id))
        
        # update hc2 vdev for hc2
        self.update_vdevice(dev_id)
        
        self.logger.debug('... clone_vdev_btn completed')

    def _get_vdev_btn_cmd_arg_filename(self,dev_id):
        """return {dev_id}.btn.cmd_arg.txt"""
        return '{dev_id}.btn.cmd_arg.txt'.format(dev_id=dev_id)
        
    def _parse_cmd_arg_text_from_file(self,btn_file):
        """return {cmd_text},{arg_text}"""
        cmd_text = arg_text = ''
        cmd_match_str = CMD_MATCH_STR
        arg_match_str = ARG_MATCH_STR
        matches = [cmd_match_str,arg_match_str]
        if os.path.exists(btn_file):
            with open(btn_file) as fh:
                t_content = fh.read().encode('utf8')
            for match_str in matches:
                items=re.findall("^%s(.+?)$" % match_str,t_content,re.MULTILINE)
                self.logger.debug('... matched items: %s' % str(items))
                if len(items) > 0:
                    if match_str == cmd_match_str:
                        cmd_text = items[-1].strip()
                    elif match_str == arg_match_str:
                        arg_text = items[-1].strip()
                else:
                    self.logger.warning('... no matched items found for pattern %s' % match_str)
        else:
            self.logger.warning('... btn_file not exist, %s' % btn_file)
            
        return '{cmd},{arg}'.format(cmd=cmd_text,arg=arg_text)
        
    def get_vdev_btn_cmd_arg_file_path(self,dev_id):
        dump_path = self._get_dev_dump_path(dev_id)
        cmd_arg_filename = self._get_vdev_btn_cmd_arg_filename(dev_id)  
        cmd_arg_file_path = os.path.join(os.path.dirname(dump_path),cmd_arg_filename)
        return cmd_arg_file_path
        
    def backup_vdev_btn_cmd_arg(self,dev_id):
        """
        backup hc2 VIRTUAL device buttons <cmdText><argText> to local backup file
            $ python api.py backup_vdev_btn_cmd_arg,<dev_id>
        create file content::
            {btn_id},{btn_caption},{cmd_text},{arg_text}
            ...
        """
        self.logger.debug('backup_vdev_btn_cmd_arg(dev_id=%s)' % dev_id)
        dev = self._get_vdev_by_id(dev_id)
        dump_path = self._get_dev_dump_path(dev_id)
        buttons = self._get_dev_all_buttons(dev)
        cmd_arg_list = []
        for button in buttons:
            btn_filename = self._get_dev_btn_dump_filename(dev_id, button)
            btn_file_path = os.path.join(dump_path,btn_filename)
            btn_cmd_arg = self._parse_cmd_arg_text_from_file(btn_file_path)
            btn_caption = button['caption']
            self.logger.debug('... btn_cmd_arg: %s' % btn_cmd_arg)
            cmd_arg_list.append('{btn_id},{btn_caption},{cmd_arg_text}'.format(
                btn_id=button['id'],btn_caption=btn_caption.encode('utf8'),
                cmd_arg_text=btn_cmd_arg))
#         cmd_arg_filename = self._get_vdev_btn_cmd_arg_filename(dev_id)  
#         cmd_arg_file_path = os.path.join(os.path.dirname(dump_path),cmd_arg_filename)
#         self.logger.debug('... cmd_arg_file_path: %s' % cmd_arg_file_path)
        cmd_arg_file_path = self.get_vdev_btn_cmd_arg_file_path(dev_id)
        t_content = '\n'.join(cmd_arg_list)
        with open(cmd_arg_file_path,'w') as fh:
            fh.write(t_content)
        self.logger.debug('... vdev_btn_cmd_arg content:\n' + t_content)        
        self.logger.debug('... backup_vdev_btn_cmd_arg completed')
        return cmd_arg_list
        
    def restore_btn_cmd_arg_value(self,local_dev_id):
        """
        update local vdev button dump file content for line cmdText = <value> and argText = <value>
            $ python api.py restore_btn_cmd_arg_value,<local_dev_id>
        parse file content::
            {btn_id},{btn_caption},{cmd_text},{arg_text}
            ...
        """
        self.logger.debug('restore_btn_cmd_arg_value(dev_id=%s)' % local_dev_id)
        dev_id = local_dev_id

        # serach *.json
        result = []
        dump_path = self._get_dev_dump_path(dev_id)
        for root, _, files in os.walk(dump_path):
            for name in files:
                if fnmatch.fnmatch(name, '*.json'):
                    result.append(os.path.join(root, name))
        if len(result) == 1:
            filename = result[0]
        else:
            self.logger.warning('... there are multiple or none dev json files exist in dump path (%s)' %
                                dump_path)
            return None
        
        # get vdev json object from local json file
        with open(filename) as fh:
            dev = json.loads(fh.read())

        # parsing cmd_arg file and update local btn dump file
        cmd_arg_filename = self._get_vdev_btn_cmd_arg_filename(dev_id)  
        cmd_arg_file_path = os.path.join(os.path.dirname(dump_path),cmd_arg_filename)
        if os.path.exists(cmd_arg_file_path):
            with open(cmd_arg_file_path,'rb') as fh:
                #t_content = fh.read().encode('utf8')
                reader = csv.reader(fh, delimiter=',', quotechar="'")
                for row in reader:
                    self.logger.debug('... row (%s)' % row)
                    btn_id,_,cmd_text,arg_text = row
                    btn_filename = self._get_dev_btn_dump_filename_by_btn_id(dev,btn_id)
                    btn_file_path = os.path.join(dump_path,btn_filename)
                    if os.path.exists(btn_file_path):
                        for line in fileinput.input(btn_file_path, inplace=1):
                            if CMD_MATCH_STR in line:
                                new_line = "%s '%s'\n" % (CMD_MATCH_STR,cmd_text)
                            elif ARG_MATCH_STR in line:
                                new_line = "%s '%s'\n" % (ARG_MATCH_STR,arg_text)
                            else:
                                new_line = line

                            if line != new_line:
                                self.logger.debug('... update [%s] to [%s]' % (
                                    line.replace('\n',''),new_line.replace('\n','')))
                            sys.stdout.write(new_line)
                    else:
                        self.logger.warning('... btn file not exist, skip' % btn_filename)
                        
        else:
            self.logger.warning('... no cmd_arg backup file exist, exit! %s' % cmd_arg_filename) 
            return None
        
        self.logger.debug('... restore_btn_cmd_arg_value completed')
        
    # # -- dump_scene
    # def _get_scene_json_dump_filename(self,scene):
    #     return '{id}.{name}.json'.format(id=scene['id'],name=scene['name'])
    #
    # def _get_scene_lua_code_filename(self,scene):
    #     return '{id}.{name}.lua'.format(id=scene['id'],name=scene['name'])
    #
    # def _dump_scene(self,dump_path,scene):
    #     """save hc2 scene json file ({scene_id}.{scene_name}.json)
    #     and lua code:
    #         {scene_id}.{scene_name}.lua
    #     """
    #
    #     # dump json
    #     filename = self._get_scene_json_dump_filename(scene)
    #     with codecs.open(os.path.join(dump_path,filename), 'wb', encoding='utf8') as fh:
    #         fh.write(json.dumps(scene,indent=2))
    #     self.logger.debug('... scene %s (%s) json dumped' % (scene['id'], scene['name']))
    #
    #     # dump scene lua code
    #     lua_code = scene['lua']
    #     lua_code = lua_code.encode('utf-8').replace('\\n','\n')
    #     filename = self._get_scene_lua_code_filename(scene)
    #     with codecs.open(os.path.join(dump_path,filename), 'wb', encoding='utf8') as fh:
    #         fh.write(lua_code.decode('utf8'))
    #     self.logger.debug('... scene lua code dumped %s' % filename)
    #
    # def dump_scene(self,scene_id):
    #     """get hc2 scene json object via HTTP API and save as local files"""
    #
    #     self.logger.debug('dump_scene %s' % scene_id)
    #
    #     hc2_scene_api = HC2APIScene(self.args,self.logger)
    #     scene = hc2_scene_api.get(key=scene_id)
    #     if scene:
    #         dump_path = self._get_scene_dump_path(scene_id,True)
    #         self._dump_scene(dump_path, scene)
    #         self.logger.debug('... dump_scene [%s] completed' % scene['name'])
    #         self.logger.debug('... dump path %s' % dump_path)
    #     else:
    #         self.logger.warning('dump_scene with id %s result None' % scene_id)
    #
    #     return scene
    #
    # # --- update_scene
    # def update_scene(self,scene_id):
    #     """update hc2 scene with local dumped files
    #     and the origin scene json object will be backup"""
    #
    #     self.logger.debug('update_scene %s with local dump files' % scene_id)
    #
    #     # check scene exist in hc2
    #     hc2_scene_api = HC2APIScene(self.args,self.logger)
    #     scene = hc2_scene_api.get(key=scene_id)
    #
    #     if scene is None:
    #         self.logger.warning('fail to get scene (id %s) json from hc2, exit' % scene_id)
    #         return None
    #
    #     # load local scene json
    #     dump_path = self._get_scene_dump_path(scene_id)
    #     filename = self._get_scene_json_dump_filename(scene)
    #     if os.path.exists(os.path.join(dump_path,filename)) == False:
    #         self.logger.warning('scene id %s dump file (%s) not exist' % (scene_id,filename))
    #         return None
    #     with open(os.path.join(dump_path,filename)) as fh:
    #         t_scene = json.loads(fh.read())
    #
    #     # update scene properties attr. lua
    #     filename = self._get_scene_lua_code_filename(scene)
    #     file_path = os.path.join(dump_path,filename)
    #     if os.path.exists(file_path):
    #         with open(file_path) as fh:
    #             lua_code = fh.read()
    #             #mainloop = mainloop.replace('\n','\\n')
    #             scene['lua'] = lua_code
    #             self.logger.debug('... scene properties lua updated')
    #     else:
    #         self.logger.warning('scene %s lua code dump file (%s) not exist' % (
    #             scene_id,file_path))
    #
    #     # update scene attr. name
    #     if scene['name'] != t_scene['name']:
    #         scene['name'] = t_scene['name']
    #         self.logger.debug('... update scene name as %s' % (
    #             scene['name'].encode('utf8')))
    #
    #     # update scene on hc2
    #     scene = hc2_scene_api.put(scene['id'],scene)
    #
    #     if scene:
    #         self.logger.debug('hc2 scene (%s:%s) update completed' % (
    #             scene['id'],scene['name'].encode('utf8')))
    #     else:
    #         self.logger.warning('hc2 scene (%s:%s) put api fail' % (
    #             t_scene['id'],t_scene['name'].encode('utf8')))
    #
    #     self.logger.debug('... update_scene completed')
    #
    #     return scene
    #
    # -- service for cmd_gvar
    
    def _get_gvar_dump_path(self,var_name,del_exist=False):
        """"""
        dump_path = os.path.join(
            self._get_dump_root(),'variables',str(var_name))
        if os.path.exists(dump_path):
            if del_exist:
                shutil.rmtree(dump_path)
                os.makedirs(dump_path)
        else:
            os.makedirs(dump_path)
        return dump_path

    def _get_gvar_json_dump_filename(self,gvar):
        """"""
        return '{name}.json'.format(name=gvar['name'])
    
    def _get_gvar_value_filename(self,gvar):
        return '{name}_value.txt'.format(name=gvar['name'])
    
    def json_str_check(self,str):
        try:
            obj = json.loads(str)
            return obj
        except ValueError:
            return None
        
    def pull_gvar(self,var_name):
        """query and save remote hc2 global variable as local json file"""
        
        self.logger.debug('pull_gvar %s with var_name' % var_name)
        
        # check var_name exist in hc2
        hc2_gvar_api = HC2APIGlobalVariable(self.args,self.logger)
        gvar = hc2_gvar_api.get(key=var_name)

        if gvar is None:
            self.logger.warning('fail to get gvar (name %s) from hc2, exit' % var_name)
            return None

        # dump json
        dump_path = self._get_gvar_dump_path(var_name=var_name,del_exist=True)
        filename = self._get_gvar_json_dump_filename(gvar)
        with codecs.open(os.path.join(dump_path,filename), 'wb', encoding='utf8') as fh: 
            fh.write(json.dumps(gvar,indent=2))
        self.logger.debug('... gvar %s json dumped' % (gvar['name']))
        
        # dump gvar value
        gvar_value = gvar['value']
        gvar_value = gvar_value.encode('utf-8').replace('\\n','\n')
        filename = self._get_gvar_value_filename(gvar)
        with codecs.open(os.path.join(dump_path,filename), 'wb', encoding='utf8') as fh: 
            obj = self.json_str_check(gvar_value)
            if obj:
                fh.write(json.dumps(obj,indent=2).decode('utf8'))
            else:
                fh.write(gvar_value.decode('utf8'))
        self.logger.debug('... gvar value dumped %s' % filename)
            
        return gvar
    
    def push_gvar(self,var_name):
        """update remote hc2 global variable with local dumped json file content"""
    
        self.logger.debug('push_gvar %s with local dump files' % var_name)
        
        # check scene exist in hc2
        hc2_gvar_api = HC2APIGlobalVariable(self.args,self.logger)
        gvar = hc2_gvar_api.get(key=var_name)

        if gvar is None:
            self.logger.warning('fail to get gvar (name %s) json from hc2, exit' % var_name)
            return None

        # load local gvar json
        dump_path = self._get_gvar_dump_path(var_name)
        filename = self._get_gvar_json_dump_filename(gvar)
        if os.path.exists(os.path.join(dump_path,filename)) == False:
            self.logger.warning('gvar %s dump file (%s) not exist' % (var_name,filename))
            return None
        with open(os.path.join(dump_path,filename)) as fh:
            t_gvar = json.loads(fh.read())
            
        # update gvar properties attr. value
        filename = self._get_gvar_value_filename(gvar)
        file_path = os.path.join(dump_path,filename)
        if os.path.exists(file_path):
            with open(file_path) as fh:
                gvar_value = fh.read()
                #mainloop = mainloop.replace('\n','\\n')
                gvar['value'] = gvar_value
                self.logger.debug('... gvar properties value updated')
        else:
            self.logger.warning('gvar %s value dump file (%s) not exist' % (
                var_name,file_path))
        
        # update scene on hc2
        hc2_gvar_api.put(var_name,gvar)

        return hc2_gvar_api.get(key=var_name)

    # -- topology
    def _get_hc2_topology_file(self):
        dump_root_path = self._get_dump_root()
        topology_file = os.path.join(dump_root_path, 'topology.json')
        return topology_file

    def read_hc2_topology(self):
        """"""
        topology_file = self._get_hc2_topology_file()
        if os.path.exists(topology_file):
            with open(topology_file) as fh:
                return json.loads(fh.read())
        else:
            self.logger.warning('read_hc2_topology fail, topology file not exist')
            return None

    def get_hc2_topology(self):
        """"""
        topology = {}

        import api_room
        topology['rooms'] = []
        rooms = api_room.HC2APIRoom(self.args, self.logger).get(key=None)
        if rooms:
            for room in rooms:
                topology['rooms'].append({'id': room['id'], 'name': room['name']})

        import api_scene
        topology['scenes'] = []
        scenes = api_scene.HC2APIScene(self.args, self.logger).get(key=None)
        if scenes:
            for scene in scenes:
                if scene['visible']:
                    topology['scenes'].append({'id': scene['id'], 'name': scene['name'], 'roomID': scene['roomID']})
                else:
                    self.logger.debug('scene id %s NOT visible, ignored' % scene['id'])

        import api_dev
        # topology['devices'] = []
        # devices = api_dev.HC2APIDevice(self.args, self.logger).get(key=None)
        # for device in devices:
        #     if device['visible']:
        #         topology['devices'].append({'id': device['id'], 'name': device['name'], 'roomID': device['roomID']})
        # import api_vdev
        # devices = api_vdev.HC2APIVirtualDevice(self.args, self.logger).get(key=None)
        # for device in devices:
        #     topology['devices'].append({'id': device['id'], 'name': device['name'], 'roomID': device['roomID']})
        return topology

    def save_hc2_topology(self, topology=None):
        """"""
        topology_file = self._get_hc2_topology_file()
        if topology is None:
            topology = self.get_hc2_topology()
        # with codecs.open(topology_file, 'wb', encoding='utf8') as fh:
        #     fh.write(json.dumps(topology, indent=2).decode('utf8'))
        with codecs.open(topology_file, 'w', encoding='utf8') as fh:
            fh.write(json.dumps(topology, indent=2, ensure_ascii=False))

        self.logger.debug('save_hc2_topology %s' % topology_file)
        return topology_file

    def _get_element_from_topology(self, topology, element_type, element_id):
        """"""
        for element in topology[element_type]:
            if element['id'] == int(element_id):
                return element
        self.logger.warning('_get_element_from_topology no matched for type %s id %s' % (element_type, element_id))
        return None

    def update_hc2_topology_file(self):
        """"""
        topology_file = self._get_hc2_topology_file()

        if not os.path.exists(topology_file):
            self.logger.debug('no local topology file exist, create new one')
            return self.save_hc2_topology()

        # update local topology newly added element attribute
        current_topology = self.get_hc2_topology()
        try:
            with open(topology_file) as fh:
                local_topology = json.loads(fh.read())
        except ValueError:
            local_topology = current_topology

        self.logger.debug('update local topology newly added element attribute ...')
        for key in local_topology.keys():
            for local_entry in local_topology[key]:
                local_entry_id = local_entry['id']
                current_entry = self._get_element_from_topology(current_topology, key, local_entry_id)
                if current_entry:
                    if local_entry['name'] == current_entry['name']:
                        for attr in local_entry.keys():
                            # if attr. name not changed, add newly added attr.
                            if attr not in current_entry.keys():
                                current_entry[attr] = local_entry[attr]
                        self.logger.debug('topology element type %s id %s name %s update with local' % (
                            key, local_entry_id, local_entry['name']
                        ))
                    else:
                        self.logger.debug('topology element type %s id %s name changed (%s -> %s)' % (
                            key, local_entry_id, local_entry['name'], current_entry['name']
                        ))
                else:
                    self.logger.debug('local topology type %s id %s removed found' % (key, local_entry_id))
        return self.save_hc2_topology(current_topology)

    def get_hc2_id_by_name(self, name, room_name=None, category='scenes', lang_code='en', topology=None):
        """
        name is hc2 device or scene name
        category in ['devices', 'scenes']
        lang_code in ['en', 'zh']
        """
        sequence_matcher_ratio_thread = 0.85

        self.logger.info('search element name [{}] with room {} category {} lang_code {} with thread {} ...'.format(
            name, room_name, category, lang_code, sequence_matcher_ratio_thread
        ))

        self.logger.debug('topology type: %s' % type(topology))
        if type(topology) is not dict:
            if topology is None:
                self.logger.debug('get_hc2_id_by_name load topology by get_hc2_topology')
                topology = self.get_hc2_topology()

            if type(topology) in [str, unicode]:
                self.logger.debug('get_hc2_id_by_name load topology file {}'.format(topology))
                with open(topology) as fh:
                    topology = json.loads(fh.read())

        lang_attr = '%s_text' % lang_code

        from difflib import SequenceMatcher

        matched_room = None
        if room_name is None:
            self.logger.debug('no room name for matching')
        else:
            self.logger.debug('room name {} for matching'.format(matched_room))
            rooms = topology.get('rooms', [])
            matched_elements = []
            for room in rooms:
                match_name = room.get(lang_attr, None)
                if match_name is None:
                    match_name = room.get('name', '')
                s = SequenceMatcher(None, room_name.lower(), match_name.lower())
                room['match_ratio'] = s.ratio()
                if room['match_ratio'] > 0.5:
                    self.logger.debug('{name} and {match_name} match ratio {ratio}'.format(
                        name=name, match_name=match_name, ratio=room['match_ratio']
                    ))
                if room['match_ratio'] >= sequence_matcher_ratio_thread:
                    matched_elements.append(room)
                    self.logger.info('room {} ({}) seems to match with {} ratio {}'.format(
                        match_name, room['id'], room_name, room['matched_ratio']
                    ))
            if len(matched_elements) == 0:
                self.logger.info('no matched room found for {} {} category {} lang_code {} found'.format(
                    name, room_name, category, lang_code
                ))
                return None
            else:
                ratio_list = [x['match_ratio'] for x in matched_elements]
                max_ratio = max(ratio_list)
                matched_room = matched_elements[ratio_list.index(max_ratio)]

        elements = []
        if matched_room is None:
            elements = topology.get(category, [])
        else:
            for element in topology.get(category, []):
                if element['roomID'] == matched_room['id']:
                    elements.append(element)

        matched_elements = []
        for element in elements:
            match_name = element.get(lang_attr, None)
            if match_name is None:
                match_name = element.get('name', '')
            s = SequenceMatcher(None, name.lower(), match_name.lower())
            element['match_ratio'] = s.ratio()
            self.logger.debug('[{}] and [{}] match ratio {}'.format(name.encode('utf8'), match_name.encode('utf8'), element['match_ratio']))

            if element['match_ratio'] >= sequence_matcher_ratio_thread:
                matched_elements.append(element)
                self.logger.info('element [{}] ({}) seems to match with [{}] ratio {}'.format(
                    match_name, element['id'], name, element['match_ratio']))

        if len(matched_elements) == 0:
            self.logger.info('no matched element found for {} room {} category {} lang_code {} found'.format(
                name, room_name, category, lang_code))
            return None
        else:
            ratio_list = [x['match_ratio'] for x in matched_elements]
            max_ratio = max(ratio_list)
            matched = matched_elements[ratio_list.index(max_ratio)]
            #matched_name = matched['name']
            self.logger.info('found hc2 matched element {name} with id {matched_id}'.format(
                name='<matched_name>', matched_id=matched['id']))
            return matched['id']

    def test(self):
        topology = '/Users/lee_shiueh/flh/projects/common/src/python/fibaro/.dump/192.168.1.18/topology.json'
        # self.get_hc2_id_by_name(name='xbmc remote cont',
        #                         category='devices',
        #                         topology=topology)
        self.get_hc2_id_by_name(name='Turn on the lights at night',
                                category='scenes',
                                topology=topology)
    @classmethod
    def main(cls):
        HC2_IP = '192.168.1.18'
        HC2_PORT = 80
        HC2_USERNAME = 'admin'
        HC2_PASSWORD = 'admin'
        GOOGLE_API_KEY = None
    
        import argparse
        
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
      
        parser.add_argument(
            '--debug',
            action='store_true',
            help='print debug message',
            default=False)
      
        parser.add_argument(
            '--print_result',
            help='print command function result',
            default=False)
      
        parser.add_argument(
            '--username',
            help='hc2 username for login, default: %(default)s',
            default=HC2_USERNAME)
          
        parser.add_argument(
            '--password',
            help='hc2 password for login, default: %(default)s',
            default=HC2_PASSWORD)
          
        parser.add_argument(
            '--hostname',
            help='hc2 hostname or IP for login, default: %(default)s',
            default=HC2_IP)
          
        parser.add_argument(
            '--hostport',
            help='hc2 web api port for access, default: %(default)s',
            default=HC2_PORT)
      
        parser.add_argument(
            '--google_api_key',
            help='google cloud api key, default: %(default)s',
            default=GOOGLE_API_KEY)

        parser.add_argument(
            'command',
            help='class pi function name and args (cmd,arg,...) as command to be executed',
            default='test')
    
        args = parser.parse_args()
        
        logging.basicConfig(
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    
        if args.debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
            logging.getLogger("requests").setLevel(logging.WARNING)
    
        logger = logging.getLogger()    
        logger.setLevel(log_level)
        logger.debug('args: %s' % str(args))
        hc2 = cls(args=args,logger=logger)
        try:
            hc2.logger.info('exec HomeCenter2 API cmd_args : %s' % args.command)
            params = args.command.split(',')
            func_name = params[0]
            if len(params) > 1:
                func_args = params[1:]
                
            cmd_func = getattr(hc2, func_name)
            if len(params) == 1: # func with no args
                result = cmd_func()
            else:
                result = cmd_func(*tuple(func_args))
            if args.print_result:
                hc2.logger.info(result)
            else:
                hc2.logger.info('== done ==')
        except:
            hc2.logger.error('exec HomeCenter2 API cmd error',exc_info=True ) 


if __name__ == '__main__':
    HC2BaseService.main()
