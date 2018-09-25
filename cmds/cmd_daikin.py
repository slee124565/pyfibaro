'''
Command Tool for Serialbox DAIKIN AirConditioner on HC2
'''

import sys
import os
import json
import shutil

from cmd_base import CMDBase

CMD_MATCH_STR = 'local cmdText ='
ARG_MATCH_STR = 'local argText ='


def _get_config_file_path():
    t_root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(t_root,'daikin.config.json')
    
class CMDDaikin(CMDBase):
    
    astr_master_name = 'master_name'
    astr_unit_name = 'unit_name'
    astr_daikin_uid = 'daikin_uid'
    astr_config_ip = 'daikin_slave_config_ip'
    
    repo_dir_name = 'repo_daikin'
    master_json_file = 'daikin.master.json.template'
    unit_json_file = 'daikin.unit.json.template'
    g_variable_names = ['AC_Ctrl_Datas','AC_Ctrl_Cmds']

    @classmethod
    def get_local_config(cls):

        CONFIG_TEMPLATE = {
            cls.astr_pi_ip: '',
            cls.astr_pi_port: 8080,
            cls.astr_modbus_id: 1,
            cls.astr_master_name: 'DAIKIN_MASTER',
            'UNITS': {}
            }
    
        config_file_path = _get_config_file_path()
        if os.path.exists(config_file_path):
            with open(config_file_path) as fh:
                t_config = json.loads(fh.read().encode('utf8'))
        else:
            t_config = CONFIG_TEMPLATE
        return dict(t_config)
    
    @classmethod
    def cmd_config_print(cls,args):
        t_config = cls.get_local_config()
#         sys.stderr.write('%s\n' % t_config[cls.astr_master_name])
        sys.stderr.write('%s\n' % json.dumps(t_config,indent=2).decode('unicode-escape').encode('utf8'))
        
    @classmethod
    def save_local_config(cls,config):

        config_file_path = _get_config_file_path()
        config_file_tmp = config_file_path + '.tmp'
        t_content = json.dumps(config,indent=2)
        with open(config_file_tmp,'wb') as fh:
            fh.write(t_content)
        shutil.move(config_file_tmp, config_file_path)
        
        cls.cmd_config_print(None)
    
    @classmethod
    def cmd_config_master(cls,args):

        t_config = cls.get_local_config()
                
        # config master name
        t_config[cls.astr_master_name] = getattr(args, cls.astr_master_name)

        # config pi ip and port
        t_config[cls.astr_pi_ip] = getattr(args, cls.astr_pi_ip)
        t_config[cls.astr_pi_port] = getattr(args, cls.astr_pi_port)
        
        # config daikin modbus id address
        t_config[cls.astr_modbus_id] = getattr(args, cls.astr_modbus_id)
        
        # save config
        cls.save_local_config(t_config)
        sys.stderr.write('success config daikin master setting\n:') 

    @classmethod
    def cmd_config_unit_salve(cls,args):

        UNIT_TEMPLATE = {
            cls.astr_unit_name: 'UNIT_NAME',
            cls.astr_config_ip: '{pi_ip}:{modbus_id}:{args.%s}' % cls.astr_daikin_uid,
            }
    
        # get config
        t_config = cls.get_local_config()

        # setup unit name
        t_unit = UNIT_TEMPLATE
        t_unit[cls.astr_unit_name] = getattr(args, cls.astr_unit_name)
        t_unit[cls.astr_pi_port] = t_config[cls.astr_pi_port]
        config_ip_str = t_unit[cls.astr_config_ip]
        t_uid = getattr(args, cls.astr_daikin_uid)
        t_unit[cls.astr_config_ip] = config_ip_str.format(
            pi_ip=t_config[cls.astr_pi_ip],
            modbus_id=t_config[cls.astr_modbus_id],
            args=args)
        #sys.stderr.write('t_unit\n%s\n' % json.dumps(t_unit,indent=2))
        t_config['UNITS'][t_uid] = t_unit
        
        # save config
        cls.save_local_config(t_config)

        sys.stderr.write('success config daikin unit setting\n:') 
    
    @classmethod
    def cmd_config_unit_rm(cls,args):
        '''remove slave unit from config'''
        # get config
        t_config = cls.get_local_config()
        t_uid = getattr(args, cls.astr_daikin_uid)
        if t_uid in t_config['UNITS'].keys():
            t_config['UNITS'].pop(t_uid)
        cls.save_local_config(t_config)

    
    @classmethod
    def _create_unit_vdevs(cls,config):
        ''''''
        t_config = config
        hc2 = config['hc2']
        t_unit = config['unit_vdev']

        t_unit_ids = []
        for uid in t_config['UNITS'].keys():
            unit_config = t_config['UNITS'][uid]
            t_unit['name'] = unit_config[cls.astr_unit_name]
            t_unit['ip'] = unit_config[cls.astr_config_ip]
            t_unit['port'] = unit_config[cls.astr_pi_port]
            
            # dev unit post api call
            t_dev = hc2.daikin_create_vdev(t_unit)
            if t_dev:
                t_unit_ids.append(str(t_dev['id']))
                t_config['UNITS'][uid]['dev_id'] = t_dev['id']
                sys.stderr.write('success to added unit[%s] vdev with hc2 id %s\n' % (
                    t_dev['name'],t_dev['id']))
            else:
                sys.stderr.write('fail to added unit[%s] vdev\n' % 
                    unit_config[cls.astr_unit_name])
        #sys.stderr.write('t_unit_ids: %s\n' % t_unit_ids)
        return t_unit_ids
    
    @classmethod
    def _create_master_vdev(cls,config):
        
        t_config = config 
        t_unit_ids = config['unit_ids']
        t_master = config['master_vdev']
        args = config['args']
        hc2 = config['hc2']
        
        # create master vdev with config
        t_config['unit_ids'] = t_unit_ids
        
        # setup master name
        t_master['name'] = t_config[cls.astr_master_name]
        
        # get master mainloop content
        mainloop = t_master['properties']['mainLoop']
        t_lines = mainloop.split('\n')
        # replace unit id list
        t_lines[11] = '    ' + ','.join(t_unit_ids)
        # replace hc2 settings
        t_lines[15] = '  hc2IP = "%s"' % getattr(args, cls.astr_hostname)
        t_lines[16] = '  hc2Port = %s' % getattr(args, cls.astr_hostport)
        t_lines[17] = '  hc2Account = "%s"' % getattr(args, cls.astr_username)
        t_lines[18] = '  hc2Password = "%s"' % getattr(args, cls.astr_password)
        
        t_master['properties']['mainLoop'] = '\n'.join(t_lines)
         
        # create master vdev on remote hc2
        t_dev = hc2.daikin_create_vdev(t_master)
        if t_dev:
            config['master_dev_id'] = t_dev['id']
            sys.stderr.write('success to added master[%s] vdev with hc2 id %s\n' % (
                t_dev['name'],t_dev['id']))
        else:
            sys.stderr.write('fail to added unit[%s] vdev\n' % 
                t_config[cls.astr_master_name])       

        return t_dev
            
    @classmethod
    def _create_variables(cls,config):
        ''''''
        var_value = ''
        hc2 = config['hc2']
        for var_name in cls.g_variable_names:
            t_var = hc2.gvar_query(var_name)
            if t_var:
                sys.stderr.write('global variable %s already exist, skip\n' % var_name)
            else:
                t_var = hc2.gvar_create({
                    "name": var_name,
                    "value": var_value,
                })
                if t_var:
                    sys.stderr.write('success to create global variable %s\n%s\n' % (t_var,json.dumps(t_var,indent=2)))
                else:
                    sys.stderr.write('fail to create global variable %s\n' % t_var)
                
    @classmethod
    def cmd_create_vdev(cls,args):
        '''create new vdev on remote hc2 with daikin vdev templates (master, unit slave)'''
        t_json_root = os.path.join(os.path.dirname(os.path.abspath(__file__)),
            cls.repo_dir_name)
        
        # get config json
        t_config = cls.get_local_config()
        t_config['args'] = args
        
        # get master vdev json
        with open(os.path.join(t_json_root,cls.master_json_file)) as fh:
            t_master = json.loads(fh.read())
        t_config['master_vdev'] = t_master
            
        # get unit vdev json
        with open(os.path.join(t_json_root,cls.unit_json_file)) as fh:
            t_unit = json.loads(fh.read())
        t_config['unit_vdev'] = t_unit
        
        # get hc2 service
        hc2 = cls.get_args_hc2(args)
        t_config['hc2'] = hc2
        
        # create units vdev with config
        t_unit_ids = cls._create_unit_vdevs(t_config)
        t_config['unit_ids'] = t_unit_ids
                
        # create master vdev with config
        t_master = cls._create_master_vdev(t_config)

        # create daikin hc2 global variables AC_Ctrl_Datas and AC_Ctrl_Cmds
        cls._create_variables(t_config)
        
        # save final config with related vdev id
        t_config.pop('hc2')
        t_config.pop('unit_ids')
        t_config.pop('unit_vdev')
        t_config.pop('master_vdev')
        t_config.pop('args')
        cls.save_local_config(t_config)
        
        # dump newly created master vdev
        #hc2.dev_pull(t_master['id'])
        
        # dump nuewly created unit slaves vdev
        #for t_id in t_unit_ids:
        #    hc2.dev_pull(t_id)
                
    @classmethod
    def cmd_parse_btn(cls,args):
        '''parse and save daikin master vdev btns cmd and args'''
        
        hc2 = cls.get_args_hc2(args)
        dev_id = getattr(args, cls.astr_dev_id)
        
        # pull dev with dev_id
        vdev = hc2.dev_pull(dev_id)
        if vdev:
            # parse btn and args with local dump files
            cmd_arg_list = hc2.daikin_parse_btn_cmd_arg(dev_id)
            
            # print parsing result
            cmd_arg_file = hc2.daikin_btn_cmd_arg_file_path(dev_id)
            sys.stderr.write('vdev btn cmd arg parse result:\n')
            for entry in cmd_arg_list:
                sys.stderr.write('%s\n' % entry)
            sys.stderr.write('daikin cmd arg saved file: %s\n' % cmd_arg_file)
            return cmd_arg_list
        else:
            sys.stderr.write('dev_pull fail with dev_id %s' % dev_id)
            return None

    @classmethod
    def cmd_update_btn(cls,args):
        '''update daikin master vdev btns cmd and args from local dumped files'''
         
        hc2 = cls.get_args_hc2(args)
        dev_id = getattr(args, cls.astr_dev_id)
        
        # update local dumped btn files with local cmd_args_file
        cmd_arg_list = hc2.daikin_update_btn_cmd_arg(dev_id)

        # print update result
        if cmd_arg_list:
            sys.stderr.write('daikin vdev btn cmd arg update result:\n')
            for entry in cmd_arg_list:
                sys.stderr.write('%s\n' % entry)
        else:
            sys.stderr.write('daikin vdev (%s) btn cmd arg update file\n' % dev_id)

        # update hc2 vdev
        vdev = hc2.vdev_update(dev_id)
        if vdev:
            sys.stderr.write('success to update hc2 daikin vdev (%s)\n' % 
                            vdev['name'].encode('utf8'))
        else:
            sys.stderr.write('fail to update hc2 daikin vdev (%s)\n' % 
                            vdev['name'].encode('utf8'))

        return vdev
        
    @classmethod
    def cmd_update_code(cls,args):
        '''update PDU code in daikin cmd_args file with module [daikind3net] define'''
        
        hc2 = cls.get_args_hc2(args)
        dev_id = getattr(args, cls.astr_dev_id)
        
        # update local dumped vdev btn files
        hc2.daikin_btn_cmd_arg_file_code_update(dev_id)
        
        # parse btn again and print result
        cmd_arg_list = hc2.daikin_parse_btn_cmd_arg(dev_id)
        sys.stderr.write('daikin vdev btn cmd code update result:\n')
        for entry in cmd_arg_list:
            sys.stderr.write('%s\n' % entry)

    @classmethod
    def get_cmd_parser(cls,base_parser,subparsers):
        cmd_parser = subparsers.add_parser(
            'daikin',
            description=__doc__,
            help='daikin vdev command tool',
            parents=[base_parser])

        scmd_subparsers = cmd_parser.add_subparsers(title='sub-command')
        
        # daikin config_master NAME PI_IP PI_PORT MODBUS_ID
        scmd_parser = scmd_subparsers.add_parser(
            'config_master',
            help='config master vdev name',
            parents=[base_parser])
        scmd_parser.add_argument(
            cls.astr_master_name,
            help='master vdev name')
        cls.add_parser_arg_pi_ip(scmd_parser)
        cls.add_parser_arg_pi_port(scmd_parser)
        cls.add_parser_arg_modbus_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_config_master)

        # daikin config_unit NAME UID
        scmd_parser = scmd_subparsers.add_parser(
            'config_unit',
            help='config slave unit vdev name and uid',
            parents=[base_parser])
        scmd_parser.add_argument(
            cls.astr_unit_name,
            help='salve unit vdev name')
        scmd_parser.add_argument(
            cls.astr_daikin_uid,
            help='unit daikin uid')
        scmd_parser.set_defaults(func=cls.cmd_config_unit_salve)

        # daikin config_unit_rm UID
        scmd_parser = scmd_subparsers.add_parser(
            'config_unit_rm',
            help=cls.cmd_config_unit_rm.__doc__,
            parents=[base_parser])
        scmd_parser.add_argument(
            cls.astr_daikin_uid,
            help='unit daikin uid')
        scmd_parser.set_defaults(func=cls.cmd_config_unit_rm)

        # daikin config
        scmd_parser = scmd_subparsers.add_parser(
            'config',
            help='print daikin config content',
            parents=[base_parser])
        scmd_parser.set_defaults(func=cls.cmd_config_print)

        # daikin create_vdev
        scmd_parser = scmd_subparsers.add_parser(
            'create_vdev',
            help='create and dump daikin master and units vdev on hc2',
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_create_vdev)
        
        # daikin parse_btn
        scmd_parser = scmd_subparsers.add_parser(
            'parse_btn',
            help=cls.cmd_parse_btn.__doc__,
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_dev_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_parse_btn)

        # daikin update_code
        scmd_parser = scmd_subparsers.add_parser(
            'update_code',
            help=cls.cmd_update_code.__doc__,
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_dev_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_update_code)

        # daikin update_btn
        scmd_parser = scmd_subparsers.add_parser(
            'update_btn',
            help=cls.cmd_update_btn.__doc__,
            parents=[base_parser])
        cls.add_parser_arg_remote_name(scmd_parser)
        cls.add_parser_arg_dev_id(scmd_parser)
        scmd_parser.set_defaults(func=cls.cmd_update_btn)

        return cmd_parser
