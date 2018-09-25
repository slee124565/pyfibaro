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
HC2_IP = '192.168.1.10'
HC2_PORT = 80
HC2_USERNAME = 'tailungfu@gmail.com'
HC2_PASSWORD = 'FLHflhtest12345'

import logging
import requests
import re
import os
import json
import shutil
import fnmatch
import fileinput
import csv, sys

CMD_MATCH_STR = 'local cmdText ='
ARG_MATCH_STR = 'local argText ='

class HomeCenter2(object):
    ''''''
    username = None
    password = None
    hostname = None
    hostport = None
    args = None

    def __init__(self,args=None,logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.username = getattr(args,'username',None)
        self.password = getattr(args,'password',None)
        self.hostname = getattr(args,'hostname',None)
        self.hostport = getattr(args,'hostport',80)
        self.api_root = 'http://%s:%s/api' % (self.hostname,self.hostport)
        self.args = args
        
        if self.username is None or self.password is None and self.hostname is None:
            raise ValueError('%s init with error username or password or hostname' %
                             self.__class__.__name__)
    
    def __str__(self, *args, **kwargs):
        return '%s (%s:%s)' % (self.__class__.__name__,self.hostname,self.hostport)
    
    # __getitem__ implement start
    def __getitem__(self,key):
        '''key: [obj_group]-[obj_id]'''
        
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
        '''return hc2 /api/devices'''
        api_url = '%s/devices' % (self.api_root)
        r = requests.get(api_url, 
                    auth=requests.auth.HTTPBasicAuth(
                        self.username,
                        self.password))
        if r.status_code == 200:
            self._devices = r.json()
            return self._devices
        else:
            self.logger.error('hc2 api (%s) call fail with requests status code %s' % (
                api_url,r.status_code))
            self.logger.warning(r.content)
            return None
        
    def _get_device_by_id(self,dev_id):
        return self['devices.'+str(dev_id)]
        
    def _get_rooms(self):
        '''TODO: return hc2 /api/rooms'''
        raise Exception
        
    def _get_scenes(self):
        '''TODO: return hc2 /api/scenes'''
        raise Exception
            
    def _get_variables(self):
        '''TODO: return hc2 /api/globalVariables'''
        raise Exception

    # __getitem__ implement end
    
    # --- dump_device
    def _get_dev_dump_path(self,dev_id,del_exist=False):
        ''' create dump folder (./.dump/hostname/devices/dev_id) if not exist'''
        dump_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),'.dump',self.hostname,'devices',str(dev_id))
        if os.path.exists(dump_path):
            if del_exist:
                shutil.rmtree(dump_path)
                os.makedirs(dump_path)
        else:
            os.makedirs(dump_path)
        return dump_path
    
    def _get_dev_json_dump_filename(self,dev):
        '''{dev_id}.{dev_name}.json'''
        dev_name = dev['name'].encode('utf8')
        if dev_name.find('/') >= 0:
            self.logger.warning('device name %s is invalid filename, replace it with underline(_)' % 
                                dev_name)
            dev_name = dev_name.replace('/','_')
        filename = '{dev_id}.{dev_name}.json'.format(dev_id=dev['id'],dev_name=dev_name)
        #filename = '{dev_id}.json'.format(dev_id=dev['id'])
        return filename
        
    def _get_dev_btn_dump_filename_by_btn_id(self,dev,btn_id):
        '''{dev_id}.button.{id}.{name}.{caption}.lua if it is lua button
        {dev_id}.button.{id}.{name}.{caption}.txt if is is sck text button
        '''
        self.logger.debug('... _get_dev_btn_dump_filename_by_btn_id(dev=%s,btn_id=%s)' % (
            dev['name'].encode('utf8'),btn_id))
        buttons = self._get_dev_all_buttons(dev)
        for button in buttons:
            if str(button['id']) == str(btn_id): 
                filename = self._get_dev_btn_dump_filename(dev['id'], button)
                self.logger.debug('... btn_dump_filename %s' % filename)
                return filename
        self.logger.warning('... can not find button dump filename!')
        return None
        
    def _get_dev_btn_dump_filename(self,dev_id,button):
        '''{dev_id}.button.{id}.{name}.{caption}.lua if it is lua button
        {dev_id}.button.{id}.{name}.{caption}.txt if is is sck text button
        '''
        btn_id = button['id']
        btn_name = button['name']
        btn_caption = button['caption']
        if btn_caption.find('/') >= 0:
            self.logger.warning('btn caption %s is invalid filename, replace it with underline(_)' %
                                btn_caption)
            btn_caption = btn_caption.replace('/','_')
        filename = u'{dev_id}.button.{id}.{name}.{caption}'.format(
            dev_id=dev_id,
            id=btn_id,
            name=btn_name,
            caption=btn_caption)
        if button['lua']:
            filename += '.lua'
        else:
            filename += '.txt'
        return filename
    
    def _get_dev_mainloop_dump_filename(self,dev):
        '''{dev_id}.main.{dev_name}.lua'''
        return '{dev_id}.main.{dev_name}.lua'.format(
            dev_id=dev['id'],dev_name=dev['name'].encode('utf8'))

    def _dump_device(self,dump_path,device):
        '''save hc2 device json file ({dev_id}.{dev_name}.json) 
        and msg of button element content:
            lua: button.{id}.{name}.{caption}.lua
            sck: button.{id}.{name}.{caption}.txt
        and mainloop code:
            main.{dev_name}.lua
        '''

        # dump json
        filename = self._get_dev_json_dump_filename(device)
        with open(os.path.join(dump_path,filename),'w') as fh:
            fh.write(json.dumps(device,indent=2))
        self.logger.debug('device %s (%s) json dumped' % (device['id'], device['name']))
        
        buttons = []
        for entry in device['properties']['rows']:
            if entry['type'] == 'button':
                buttons += entry['elements']
            
        # dump buttons
        if len(buttons) > 0:
            for button in buttons:
                btn_msg = button['msg']
                btn_msg = btn_msg.encode('utf-8')
                btn_caption = button['caption']
                filename = self._get_dev_btn_dump_filename(device['id'],button)
                with open(os.path.join(dump_path,filename),'w') as fh:
                    fh.write(btn_msg.replace('\\n','\n'))
                self.logger.debug('dev btn %s msg dumped' % btn_caption)    

        # dump main loop
        mainloop = device['properties']['mainLoop']
        mainloop = mainloop.encode('utf-8')
        filename = self._get_dev_mainloop_dump_filename(device)
        with open(os.path.join(dump_path,filename),'w') as fh:
            fh.write(mainloop.replace('\\n','\n'))
        self.logger.debug('dev mainloop code dumped %s' % filename)
            

    def dump_device(self,dev_id):
        '''get hc2 device json object via HTTP API and save as local files'''
        
        self.logger.info('dump_device %s' % dev_id)
         
        device = self._get_device_by_id(dev_id)
        if device:
            dump_path = self._get_dev_dump_path(dev_id,True)
            self._dump_device(dump_path, device)
            self.logger.info('... dump_device [%s] completed' % device['name'])
        else:
            self.logger.warning('dump_device with id %s result None')
            
        return device
            
    # --- update_vdevice
    def _get_dev_bak_path(self,dev_id,del_exist=False):
        ''' create backup folder (./.dump/hostname/devices/dev_id.origin) if not exist'''
        bak_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),'.dump',
            self.hostname,'devices','%s.origin' % str(dev_id))
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
        api_url = 'http://%s:%s/api/virtualDevices/%s' % (self.hostname,self.hostport,dev['id'])
        r = requests.put(api_url, 
                    data=json.dumps(dev),
                    auth=requests.auth.HTTPBasicAuth(self.username,self.password)) 
        if r.status_code == 200:
            self.logger.debug('hc2 virtual device (%s:%s) update completed' % (
                dev['id'],dev['name'].encode('utf8')))
            hc2_resp = r.json()
            return hc2_resp
        else:
            self.logger.warning('hc2 virtual device (%s:%s) PUT api fail, status code %s' % (
                dev['id'],dev['name'].encode('utf8'),r.status_code))
            self.logger.warning(r.content)
            return None
            
    def update_vdevice(self,dev_id):
        '''update hc2 virtual device with local dumped files
        and the origin virtual device json object will be backup'''

        self.logger.info('update_vdevice %s with local dump files' % dev_id)
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
                        self.logger.info('... properties %s value %s updated' % (
                            key,t_dev['properties'][key]))

        # update dev properties attr. ip, and port
        for key in ['port','ip']:
            if dev['properties'][key] != t_dev['properties'][key]:
                dev['properties'][key] = t_dev['properties'][key]
                self.logger.info('... properties %s value %s updated' % (
                    key,t_dev['properties'][key]))
            
        # update dev properties attr. mainLoop
        filename = self._get_dev_mainloop_dump_filename(dev)
        file_path = os.path.join(dump_path,filename)
        if os.path.exists(file_path):
            with open(file_path) as fh:
                mainloop = fh.read()
                #mainloop = mainloop.replace('\n','\\n')
                dev['properties']['mainLoop'] = mainloop
                self.logger.info('... properties mainLoop updated')
        else:
            self.logger.warning('vdevice %s mainloop dump file (%s) not exist' % (
                dev_id,file_path))
        
        # update dev properties attr. rows button elements
        buttons = self._get_dev_all_buttons(dev)
        for button in buttons:
            self.logger.debug('... select button id %s with caption [%s]' % (button['id'],button['caption']))
        
        # update buttons msg
        for button in buttons:
            self._button_update_with_dump_file(button,dev_id)
        self.logger.info('... properties row element buttons updated')
        
        # update dev attr. name
        if dev['name'] != t_dev['name']:
            dev['name'] = t_dev['name']
            self.logger.info('... update vdev name as %s' % (dev['name'].encode('utf8')))
        
        # update vdev on hc2 vdevice
        self._update_vdev_on_hc2(dev)      
        
        self.logger.info('... update_vdevice completed')
            
    def _test_update_vdevice(self):  
        dev_id = 1458
        self.update_vdevice(dev_id)
    
    # --- set vdev button attr lua, waitForResponse
    def set_vdevice_btns(self,dev_id,set_lua=False,set_wait=False):
        '''update hc2 virtual device all buttons lua and waitForResponse attr.'''
        
        self.logger.info('set_vdevice_btns %s with lua: %s and waitForResponse: %s' % (
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
        self.logger.info('... hc2 virtual device updated')
        
        # save new vdev from hc2
        dump_path = self._get_dev_dump_path(dev_id, del_exist=True)
        self._dump_device(dump_path, new_dev)
        
        self.logger.info('... set_vdevice_btns completed')
        
    # --- post vdev
    def clone_vdevice(self,local_dev_id):
        '''create a new hc2 virtual device with local existing vdev json dumped file'''
        
        self.logger.info('clone_vdevice with local dumped dev id %s' % local_dev_id)
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
        api_url = 'http://%s:%s/api/virtualDevices/' % (self.hostname,self.hostport)
        r = requests.post(api_url, 
                    data=json.dumps(t_dev),
                    auth=requests.auth.HTTPBasicAuth(self.username,self.password)) 
        if r.status_code == 201:
            new_dev = r.json()
            self.logger.info('... new added vdev id is %s' % new_dev['id'])
        else:
            self.logger.warning('hc2 virtual device (%s:%s) post api fail, status code %s' % (
                src_dev['id'],src_dev['name'].encode('utf8'),r.status_code))
            self.logger.warning(r.content)
            return None
        
        # update new_dev content with base_dev
        t_dev['id'] = new_dev['id']
        new_dev = self._update_vdev_on_hc2(t_dev)
        
        self.logger.info('... clone_vdevice completed')
        return new_dev   
    
    def clone_vdev_btn(self,dev_id,src_btn_id,dest_btn_id=None):
        '''clone hc2 VIRTUAL device all buttons code from one of its existing button
            $ python api.py clone_vdev_btn,<dev_id>,<src_btn_id>,<dest_btn_id>
        '''
        
        self.logger.info('clone_vdev_btn with dev_id %s, src_btn_id %s,dest_btn_id %s' % (
            dev_id,src_btn_id,dest_btn_id))
        
        # dump vdev from hc2
        dev = self.dump_device(dev_id)
        
        # get src btn dump filename
        src_btn_filename = self._get_dev_btn_dump_filename_by_btn_id(dev,src_btn_id)
        self.logger.info('... src btn filename %s' % src_btn_filename)
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
                    self.logger.info('... cp src btn (%s) dump file for all btn (%s) dump file' % (
                        src_btn_id,t_btn_id))
                else:
                    self.logger.debug('... skip cp src btn (%s) dump file for all btn (%s) dump file' % (
                        src_btn_id,t_btn_id))
            else:
                if str(dest_btn_id) == str(button['id']):
                    shutil.copyfile(src_btn_file_path, dest_btn_file_path)
                    self.logger.info('... cp src btn (%s) dump file for dest btn (%s) dump file' % (
                        src_btn_id,dest_btn_id))
                else:
                    self.logger.debug('... skip cp src btn (%s) dump file for dest btn (%s) dump file' % (
                        src_btn_id,dest_btn_id))
        
        # update hc2 vdev for hc2
        self.update_vdevice(dev_id)
        
        self.logger.info('... clone_vdev_btn completed')

    def _get_vdev_btn_cmd_arg_filename(self,dev_id):
        '''return {dev_id}.btn.cmd_arg.txt'''
        return '{dev_id}.btn.cmd_arg.txt'.format(dev_id=dev_id)
        
    def _parse_cmd_arg_text_from_file(self,btn_file):
        '''return {cmd_text},{arg_text}'''
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
        
    def backup_vdev_btn_cmd_arg(self,dev_id):
        '''
        backup hc2 VIRTUAL device buttons <cmdText><argText> to local backup file
            $ python api.py backup_vdev_btn_cmd_arg,<dev_id>
        create file content::
            {btn_id},{btn_caption},{cmd_text},{arg_text}
            ...
        '''
        self.logger.info('backup_vdev_btn_cmd_arg(dev_id=%s)' % dev_id)
        dev = self._get_vdev_by_id(dev_id)
        dump_path = self._get_dev_dump_path(dev_id)
        buttons = self._get_dev_all_buttons(dev)
        cmd_arg_list = []
        for button in buttons:
            btn_filename = self._get_dev_btn_dump_filename(dev_id, button)
            btn_file_path = os.path.join(dump_path,btn_filename)
            btn_cmd_arg = self._parse_cmd_arg_text_from_file(btn_file_path)
            btn_caption = button['caption'].encode('utf8')
            self.logger.debug('... btn_cmd_arg: %s' % btn_cmd_arg)
            cmd_arg_list.append('{btn_id},{btn_caption},{cmd_arg_text}'.format(
                btn_id=button['id'],btn_caption=btn_caption,
                cmd_arg_text=btn_cmd_arg))
        cmd_arg_filename = self._get_vdev_btn_cmd_arg_filename(dev_id)  
        cmd_arg_file_path = os.path.join(os.path.dirname(dump_path),cmd_arg_filename)
        self.logger.info('... cmd_arg_file_path: %s' % cmd_arg_file_path)
        t_content = '\n'.join(cmd_arg_list)
        with open(cmd_arg_file_path,'w') as fh:
            fh.write(t_content)
        self.logger.debug('... vdev_btn_cmd_arg content:\n' + t_content)        
        self.logger.info('... backup_vdev_btn_cmd_arg completed')
        return cmd_arg_list
        
    def restore_btn_cmd_arg_value(self,local_dev_id):
        '''
        update local vdev button dump file content for line cmdText = <value> and argText = <value>
            $ python api.py restore_btn_cmd_arg_value,<local_dev_id>
        parse file content::
            {btn_id},{btn_caption},{cmd_text},{arg_text}
            ...
        '''
        self.logger.info('restore_btn_cmd_arg_value(dev_id=%s)' % local_dev_id)
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
                                self.logger.info('... update [%s] to [%s]' % (
                                    line.replace('\n',''),new_line.replace('\n','')))
                            sys.stdout.write(new_line)
                    else:
                        self.logger.warning('... btn file not exist, skip' % btn_filename)
                        
        else:
            self.logger.warning('... no cmd_arg backup file exist, exit! %s' % cmd_arg_filename) 
            return None
        
        self.logger.info('... restore_btn_cmd_arg_value completed')
       

if __name__ == '__main__':

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
        'command',
        help='class pi function name and args (cmd,arg,...) as command to be executed',
        default=None)

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
    hc2 = HomeCenter2(args=args,logger=logger)
    try :
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
        
        
        
        

    