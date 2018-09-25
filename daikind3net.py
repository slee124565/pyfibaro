#!/usr/bin/env python

import json
import logging
from retrying import retry
from time import sleep
import minimalmodbus
import types


FUNC_CODE_READ = 0x04
FUNC_CODE_WRITE = 0x06
FUNC_CODE_WRITE_MULTI = 0x10

INPUT_REGISTER_ADDRESS_BASE = 30001
HOLDING_REGISTER_ADDRESS_BASE = 40001

ADAPTER_SETTINGS_MANAGED = 0x0001
ADAPTER_SETTINGS_MASTER = 0x0100
ADAPTER_SETTINGS_COMMUNICATION_START = 0x8000

FAN_CONTROL_FLAG = 0x0060
FAN_DIRECTION_ID_P0_HORIZONTAL = 0x0000
FAN_DIRECTION_ID_P1 = 0x0100
FAN_DIRECTION_ID_P2 = 0x0200
FAN_DIRECTION_ID_P3 = 0x0300
FAN_DIRECTION_ID_P4_VERTICAL = 0x0400
FAN_DIRECTION_ID_STOP = 0x0600
FAN_DIRECTION_ID_SWING = 0x0700
FAN_VOLUME_ID_LOW = 0x1000
FAN_VOLUME_ID_MEDIUM = 0x3000
FAN_VOLUME_ID_HIGHT = 0x5000

OP_MODE_ID_FAN = 0x00
OP_MODE_ID_HEATING = 0x01
OP_MODE_ID_COOLING = 0x02
OP_MODE_ID_AUTO = 0x03
OP_MODE_ID_SETPOINT = 0x06
OP_MODE_ID_DRY = 0x07

OP_STATUS_ID_DONT_CARE = 0x0000
OP_STATUS_ID_HEATING = 0x0100
OP_STATUS_ID_COOLING = 0x0200

UID_TOTAL_LIST = range(100,116)

WRITE_REGISTER_OK_DICT = {
    'result': 'OK',
    'text': 'write register'
    }

MAX_RETRY_TIME=3
RETRY_DELAY=1500
ADAPTER_SILENT_INTERVAL=0.5

class DaikinD3Net(minimalmodbus.Instrument):
    '''Instrument class for Daikin DIII-NET Modbus Communication Adaptor
    
    Communicates via Modbus RTU protocol (via RS485), using the *MinimalModbus* Python module

    Args:
        * portname (str): port name
        * slaveaddress (int): slave address in range 1 to 247
        
    Implemented with these function codes (in decimal):

    ==================  ====================
    Description         Modbus function code
    ==================  ====================
    Read registers      4 (0x04)
    Write registers     06 (0x06)
    ==================  ====================

    '''
    
    unit_list = []
    
    def __init__(self,args,logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.args = args

        minimalmodbus.Instrument.__init__(self,self.args.SERIALPORT,args.SLAVE_ADDR)
        self.serial.baudrate = args.BAUDRATE
        self.serial.parity = args.parity
        self.serial.stopbits = args.stopbits
        self.serial.timeout = 0.05
        self.debug = args.debug
        self.mode = minimalmodbus.MODE_RTU
            
    def clone_with_slaveaddress(self,slaveaddress):
        '''fork another instr with different modbus address'''
        if self.address == slaveaddress:
            self.logger.warning('clone with SAME slaveaddress, return self')
            return self
        else:
            import copy
            new_args = copy.deepcopy(self.args)
            setattr(new_args,'SLAVE_ADDR',slaveaddress)
            self.logger.debug('new args: %s' % str(new_args))
            t_cls = self.__class__
            instr = t_cls(args=new_args,logger=self.logger)
            self.logger.debug('%s clone_by_slaveaddress %s' % (t_cls.__name__,slaveaddress))
            return instr
        
    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def get_adaptor_status(self):
        '''get Daikin-DIII-Adaptor current status with (code,text) json object'''
        try:
            registeraddress = 30001 - INPUT_REGISTER_ADDRESS_BASE
            value = self.read_register(registeraddress,functioncode=FUNC_CODE_READ)
            adaptor_status = {
                'code': value & 0x01,
                'text': 'Ready' if (value & 0x01) == 1 else 'Not ready'
                }
            return adaptor_status
        except:
            self.logger.error('minimalmodbus instrument exception',exc_info=True)
            raise Exception('get_adaptor_status error')

    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def get_indoor_units_connection_status(self):
        '''get connected indoor units current connection status with (code,text) json object'''
        try:
            registeraddress = 30002 - INPUT_REGISTER_ADDRESS_BASE
            value = self.read_register(registeraddress,functioncode=FUNC_CODE_READ)
            units_conn_status = {}
            mask = 0x01
            for uid in range(100,116):
                units_conn_status[str(uid)] = {
                    'code': (value & mask) >> (uid - 100),
                    'text': 'connnected' if (value & mask) > 0 else 'unconnected'
                    }
                mask = (mask << 1)
            return units_conn_status
        except:
            self.logger.error('minimalmodbus instrument exception',exc_info=True)
            raise Exception('get_indoor_units_connection_status')
    
    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def get_indoor_units_communication_status(self):
        '''get connected indoor units current communication status with (code,text) json object'''
        try:
            registeraddress = 30006 - INPUT_REGISTER_ADDRESS_BASE
            value = self.read_register(registeraddress,functioncode=FUNC_CODE_READ)
            units_comm_status = {}
            mask = 0x01
            for uid in range(100,116):
                units_comm_status[str(uid)] = {
                    'code': (value & mask) >> (uid - 100),
                    'text': 'normal' if (value & mask) > 0 else 'communication error'
                    }
                mask = (mask << 1)
            return units_comm_status
        except:
            self.logger.error('minimalmodbus instrument exception',exc_info=True)
            raise Exception('get_indoor_units_communication_status error')
    
    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def get_indoor_unit_capability_information(self,uid):
        '''get connected indoor units capability detail with (code,text) json object'''
        try:
            if int(uid) in UID_TOTAL_LIST:
                registeraddress = 31001 + 3*(int(uid) - 100) - INPUT_REGISTER_ADDRESS_BASE
                values = self.read_registers(registeraddress,3,functioncode=FUNC_CODE_READ)
                #self.logger.debug('read_registers values:')
                #for n in values:
                #    self.logger.debug('{:016b}'.format(n))
                unit_capability = {}
                unit_capability['fan_mode'] = {
                    'code': (values[0] & 0b0000000000000001),
                    'text': 'exist' if (values[0] & 0b0000000000000001) else 'not exist'
                    }
                unit_capability['cooling_mode'] = {
                    'code': (values[0] & 0b0000000000000010) >> 1,
                    'text': 'exist' if (values[0] & 0b0000000000000010) else 'not exist'
                    }
                unit_capability['heating_mode'] = {
                    'code': (values[0] & 0b0000000000000100) >> 2,
                    'text': 'exist' if (values[0] & 0b0000000000000100) else 'not exist'
                    }
                unit_capability['auto_mode'] = {
                    'code': (values[0] & 0b0000000000001000) >> 3,
                    'text': 'exist' if (values[0] & 0b0000000000001000) else 'not exist'
                    }
                unit_capability['dry_mode'] = {
                    'code': (values[0] & 0b0000000000010000) >> 4,
                    'text': 'exist' if (values[0] & 0b0000000000010000) else 'not exist'
                    }
                unit_capability['fan_direction_level'] = {
                    'code': (values[0] & 0b0000011100000000) >> 8,
                    'text': '%s step' % (values[0] & 0b0000000000010000)
                    }
                unit_capability['fan_driection'] = {
                    'code': (values[0] & 0b0000100000000000) >> 11,
                    'text': 'exist' if (values[0] & 0b0000100000000000) else 'not exist'
                    }
                unit_capability['fan_volume_level'] = {
                    'code': (values[0] & 0b0111000000000000) >> 12,
                    'text': '%s step' % ((values[0] & 0b0111000000000000) >> 12)
                    }
                unit_capability['fan_volume'] = {
                    'code': (values[0] & 0b1000000000000000) >> 15,
                    'text': 'exist' if (values[0] & 0b1000000000000000) else 'not exist'
                    }

                unit_capability['cooling_setpoint'] = {
                    'upper_limit': {
                        'code': (values[1] & 0x00ff) if (values[1] & 0x00ff) <= 127\
                                                else (-1)*(256-(values[1] & 0x00ff)),
                        'text': None
                        },
                    'lower_limit': {
                        'code': ((values[1] & 0xff00) >> 8) if (((values[1] & 0xff00) >> 8) <= 127) \
                                                else (-1)*(256-((values[1] & 0xff00) >> 8)),
                        'text': None
                        }
                    }
                
                unit_capability['heating_setpoint'] = {
                    'upper_limit': {
                        'code': (values[2] & 0x00ff) if (values[2] & 0x00ff) <= 127\
                                                else (-1)*(256-(values[2] & 0x00ff)),
                        'text': None
                        },
                    'lower_limit': {
                        'code': ((values[2] & 0xff00) >> 8) if (((values[2] & 0xff00) >> 8) <= 127) \
                                                else (-1)*(256-((values[2] & 0xff00) >> 8)),
                        'text': None
                        }
                    }

                return unit_capability
            else:
                raise Exception('unit id (%s) invalid' % uid)
        except:
            self.logger.error('minimalmodbus instrument exception',exc_info=True)
            raise Exception('get_indoor_unit_capability_information error')
        
    def _parsing_unit_status_values(self,values=[]):
        '''parsing register values for a unit status'''
        
        self.logger.debug('parsing unit status values: %s' % 
                          ','.join('0x{:02x}'.format(n) for n in values))
        if len(values) != 6:
            self.logger.error('param values len not correct' % len(values))
            raise Exception('_parsing_unit_status_values param error')
        
        unit_status = {}
        unit_status['on_off'] = {
            'code': (values[0] & 0x01),
            'text': 'on' if (values[0] & 0x01) else 'off'
            }
        
        unit_status['forced_off'] = {
            'code': ((values[0] & 0x04) >> 2),
            'text': 'forced off' if (values[0] & 0x04) else 'none'
            }
        
        unit_status['fan_direction'] = {
            'code': ((values[0] & 0x0700) >> 8),
            'text': 'p%s' % ((values[0] & 0x0700) >> 8)
            }
        if unit_status['fan_direction']['code'] == 7:
            unit_status['fan_direction']['text'] = 'swing'

        unit_status['fan_volume'] = {
            'code': ((values[0] & 0x7000) >> 12),
            }
        if unit_status['fan_volume']['code'] == 1:
            unit_status['fan_volume']['text'] = 'l'
        elif unit_status['fan_volume']['code'] == 3:
            unit_status['fan_volume']['text'] = 'm'
        elif unit_status['fan_volume']['code'] == 5:
            unit_status['fan_volume']['text'] = 'h'
        else:
            unit_status['fan_volume']['text'] = None
            
        unit_status['op_mode'] = {
            'code': ((values[1] & 0x000f)),
            }
        if unit_status['op_mode']['code'] == 0:
            unit_status['op_mode']['text'] = 'fan'
        elif unit_status['op_mode']['code'] == 1:
            unit_status['op_mode']['text'] = 'heating'
        elif unit_status['op_mode']['code'] == 2:
            unit_status['op_mode']['text'] = 'cooling'
        elif unit_status['op_mode']['code'] == 3:
            unit_status['op_mode']['text'] = 'auto'
        elif unit_status['op_mode']['code'] == 7:
            unit_status['op_mode']['text'] = 'dry'
        else:
            unit_status['op_mode']['text'] = None
            
        unit_status['filter_sign'] = {
            'code': ((values[1] & 0x00f0) >> 4),
            'text': 'off' if ((values[1] & 0x00f0) >> 4) else 'off'
            }

        unit_status['op_status'] = {
            'code': ((values[1] & 0x0f00) >> 8),
            }
        if unit_status['op_status']['code'] == 0:
            unit_status['op_status']['text'] = 'fan'
        elif unit_status['op_status']['code'] == 1:
            unit_status['op_status']['text'] = 'heating'
        elif unit_status['op_status']['code'] == 2:
            unit_status['op_status']['text'] = 'cooling'
        else:
            unit_status['op_status']['text'] = None
        
        unit_status['master_slave'] = {
            'code': ((values[1] & 0xc000) >> 14),
            }
        if unit_status['master_slave']['code'] == 0:
            unit_status['master_slave']['text'] = 'not decided'
        elif unit_status['master_slave']['code'] == 1:
            unit_status['master_slave']['text'] = 'slave'
        elif unit_status['master_slave']['code'] == 2:
            unit_status['master_slave']['text'] = 'master'
        else:
            unit_status['master_slave']['text'] = None

        unit_status['setpoint'] = {
            'code': values[2],
            'text': 'off' if ((values[1] & 0x00f0) >> 4) else 'off'
            }
        if (unit_status['setpoint']['code'] <= 0x7fff):
            unit_status['setpoint']['text'] = 0.1 * unit_status['setpoint']['code']
        else:
            unit_status['setpoint']['text'] = (-0.1) * (0xffff-unit_status['setpoint']['code'])

        unit_status['err_code_1'] = {
            'code': ((values[3] & 0x000f)),
            'text': ((values[3] & 0x000f))
            }
        unit_status['err_code_2'] = {
            'code': ((values[3] & 0x01f0) >> 4),
            'text': ((values[3] & 0x01f0) >> 4)
            }
        unit_status['malfunction'] = {
            'code': ((values[3] & 0x0200) >> 9),
            'text': 'malfunction' if ((values[3] & 0x0200) >> 9) else 'normal' 
            }
        unit_status['warning'] = {
            'code': ((values[3] & 0x0400) >> 10),
            'text': 'warning' if ((values[3] & 0x0400) >> 10) else 'normal' 
            }

        unit_status['room_temperature'] = {
            'code': values[4],
            'text': 'off' if ((values[1] & 0x00f0) >> 4) else 'off'
            }
        if (unit_status['room_temperature']['code'] <= 0x7fff):
            unit_status['room_temperature']['text'] = 0.1 * unit_status['room_temperature']['code']
        else:
            unit_status['room_temperature']['text'] = (-0.1) * (0xffff-unit_status['room_temperature']['code'])
        unit_status['room_temperature']['text'] = '{:.2f}'.format(unit_status['room_temperature']['text'])
        
        unit_status['sensor_error'] = {
            'code': ((values[5] & 0x0100) >> 8),
            'text': 'error' if ((values[5] & 0x0100) >> 8) else 'normal' 
            }
        unit_status['sensor_data_recv'] = {
            'code': ((values[5] & 0x8000) >> 15),
            'text': 'received' if ((values[5] & 0x8000) >> 15) else 'not yet' 
            }
        return unit_status
        
    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def get_indoor_unit_status_information(self,uid,int_values_mode=False):
        '''get indoor unit current status detail with (code,text) json object'''
        try:
            if int(uid) in UID_TOTAL_LIST:
                registeraddress = 32001 + 6*(int(uid) - 100) - INPUT_REGISTER_ADDRESS_BASE
                values = self.read_registers(registeraddress,6,functioncode=FUNC_CODE_READ)

                if int_values_mode:
                    return values
                unit_status = self._parsing_unit_status_values(values)
                return unit_status
            else:
                raise Exception('unit id (%s) invalid' % uid)
        except:
            self.logger.error('get_indoor_unit_status_information error', exc_info=True)
            raise Exception('get_indoor_unit_status_information error')
        
    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def get_all_status_information(self):
        '''get all indoor unit current status detail with (code,text) json object'''
        try:
            registeraddress = 32001 
            values = self.read_registers(registeraddress,96,functioncode=FUNC_CODE_READ)
            all_status = {}
            for uid in UID_TOTAL_LIST:
                index = (int(uid)-100)
                if len(values) < (index+6):
                    self.logger.debug('reach register return values end, break loop')
                    break
                unit_values = values[index:index+6]
                unit_status = self._parsing_unit_status_values(unit_values)
                all_status[str(uid)] = unit_status
            return all_status
        except:
            self.logger.error('get_all_status_information error', exc_info=True)
            raise Exception('get_all_status_information error')

    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def set_adaptor_inital_settings(self,is_managed,is_master,is_comm_start):
        '''set Daikin-DIII-Adaptor initial settings'''
        try:
            registeraddress = 40001 - HOLDING_REGISTER_ADDRESS_BASE
            value = 0x0000
            if is_managed:
                value |= 0x0001
            if is_master:
                value |= 0x0100
            if is_comm_start:
                value |= 0x8000
            self.write_register(registeraddress, value, functioncode=FUNC_CODE_WRITE)
            return WRITE_REGISTER_OK_DICT
        except:
            self.logger.error('Failed to write to instrument',exc_info=True)
            raise Exception('set_adaptor_inital_settings error')          
        
    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def _set_indoor_unit_value_1(self,uid,value):
        '''(internal function) write DIII 1st Register with hex value'''
        try:
            if int(uid) in UID_TOTAL_LIST:
                registeraddress = 42001 + 3*(int(uid) - 100) - HOLDING_REGISTER_ADDRESS_BASE
                self.write_register(registeraddress, value)
                return WRITE_REGISTER_OK_DICT
            else:
                raise Exception('unit id (%s) invalid' % uid)
        except:
            self.logger.error('_set_indoor_unit_value_1 error',exc_info=True)
            raise Exception('_set_indoor_unit_value_1 error')

    def set_indoor_unit_power(self,uid,is_on=None):
        '''(internal funciton) set indoor unit power to on or off'''
        status_values = self.get_indoor_unit_status_information(uid, int_values_mode=True)
        current_value = status_values[0]
        sleep(ADAPTER_SILENT_INTERVAL)
        self._set_indoor_unit_value_1(uid, current_value)
        if is_on is None:
            if (current_value & 0x01):
                is_on = False
            else:
                is_on = True
        if is_on:
            new_value = (current_value & 0xfffe) | 0x0001
        else: 
            new_value = (current_value & 0xfffe) | 0x0000 
        return self._set_indoor_unit_value_1(uid, new_value)    
    def set_indoor_unit_power_on(self,uid):
        '''set a indoor unit power to on by uid'''
        self.logger.debug('set_indoor_unit_power_on %s' % uid)
        return self.set_indoor_unit_power(uid, is_on=True)
    def set_indoor_unit_power_off(self,uid):
        '''set a indoor unit power to off by uid'''
        self.logger.debug('set_indoor_unit_power_off %s' % uid)
        return self.set_indoor_unit_power(uid, is_on=False)

    def set_indoor_unit_fan_direction_id(self,uid,fan_direction_id):
        '''set a indoor unit fan direction to direction code by uid'''
        self.logger.debug('set_indoor_unit_fan_direction_id (%s,%s)' % (uid,fan_direction_id))
        status_values = self.get_indoor_unit_status_information(uid, int_values_mode=True)
        current_value = status_values[0]
        sleep(ADAPTER_SILENT_INTERVAL)
        current_value |= FAN_CONTROL_FLAG
        self._set_indoor_unit_value_1(uid, current_value)
        new_value = (current_value & 0xf8ff) | (fan_direction_id << 8) 
        return self._set_indoor_unit_value_1(uid, new_value)    

    def set_indoor_unit_fan_volume_id(self,uid,fan_volume_id):
        '''set a indoor unit fan direction to fan volume code by uid'''
        self.logger.debug('set_indoor_unit_fan_volume_id (%s,%s)' % (uid,fan_volume_id))
        status_values = self.get_indoor_unit_status_information(uid, int_values_mode=True)
        current_value = status_values[0]
        sleep(ADAPTER_SILENT_INTERVAL)
        current_value |= FAN_CONTROL_FLAG
        self._set_indoor_unit_value_1(uid, current_value)
        new_value = (current_value & 0x8fff) | FAN_CONTROL_FLAG | (fan_volume_id << 12) 
        return self._set_indoor_unit_value_1(uid, new_value)    
        
    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def _set_indoor_unit_value_2(self,uid,value):
        '''(internal function) write DIII 2nd Register with hex value'''
        try:
            if int(uid) in UID_TOTAL_LIST:
                registeraddress = 42002 + 3*(int(uid) - 100) - HOLDING_REGISTER_ADDRESS_BASE
                self.write_register(registeraddress, value)
                return WRITE_REGISTER_OK_DICT
            else:
                raise Exception('unit id (%s) invalid' % uid)
        except:
            self.logger.error('_set_indoor_unit_value_2 error',exc_info=True)
            raise Exception('_set_indoor_unit_value_2 error')
    def _set_indoor_unit_op_mode(self,uid,op_mode_id):
        '''(internal function) set a indoor unit operation mode to op_mode code by uid'''
        self.logger.debug('_set_indoor_unit_op_mode (%s,%s)' % (uid,op_mode_id))
        status_values = self.get_indoor_unit_status_information(uid, int_values_mode=True)
        current_value = status_values[1]
        self._set_indoor_unit_value_2(uid, current_value)
        sleep(ADAPTER_SILENT_INTERVAL)
        new_value = (current_value & 0xfff0) | op_mode_id 
        return self._set_indoor_unit_value_2(uid, new_value)    
    def set_indoor_unit_op_mode_fan(self,uid):
        '''set a indoor unit to fan mode code by uid'''
        self.logger.debug('set_indoor_unit_op_mode_fan %s' % uid)
        return self._set_indoor_unit_op_mode(uid,OP_MODE_ID_FAN)
    def set_indoor_unit_op_mode_heating(self,uid):
        '''set a indoor unit to heating mode code by uid'''
        self.logger.debug('set_indoor_unit_op_mode_fan %s' % uid)
        return self._set_indoor_unit_op_mode(uid,OP_MODE_ID_HEATING)
    def set_indoor_unit_op_mode_cooling(self,uid):
        '''set a indoor unit to cooling mode code by uid'''
        self.logger.debug('set_indoor_unit_op_mode_cooling %s' % uid)
        return self._set_indoor_unit_op_mode(uid,OP_MODE_ID_COOLING)
    def set_indoor_unit_op_mode_auto(self,uid):
        '''set a indoor unit to auto mode code by uid'''
        self.logger.debug('set_indoor_unit_op_mode_auto %s' % uid)
        return self._set_indoor_unit_op_mode(uid,OP_MODE_ID_AUTO)
    def set_indoor_unit_op_mode_dry(self,uid):
        '''set a indoor unit to dry mode code by uid'''
        self.logger.debug('set_indoor_unit_op_mode_dry %s' % uid)
        return self._set_indoor_unit_op_mode(uid,OP_MODE_ID_DRY)
    def _set_indoor_unit_filter_sign(self,uid,reset_value):
        '''(internal function) reset a indoor unit filter sign by uid'''
        self.logger.debug('_set_indoor_unit_filter_sign (%s,%s)' % (uid,reset_value))
        status_values = self.get_indoor_unit_status_information(uid, int_values_mode=True)
        current_value = status_values[1]
        self._set_indoor_unit_value_2(uid, current_value)
        sleep(ADAPTER_SILENT_INTERVAL)
        new_value = (current_value & 0xff0f) | reset_value 
        return self._set_indoor_unit_value_2(uid, new_value)    
    def set_indoor_unit_filter_sign_reset(self,uid):
        '''reset a indoor unit filter sign by uid'''
        self.logger.debug('set_indoor_unit_filter_sign_reset (%s)' % (uid))
        FILTER_SIGN_FLAG_RESET = 0x00f0
        self._set_indoor_unit_filter_sign(uid, FILTER_SIGN_FLAG_RESET)
        sleep(ADAPTER_SILENT_INTERVAL)
        FILTER_SIGN_FLAG_NONE = 0x0000
        return self._set_indoor_unit_filter_sign(uid, FILTER_SIGN_FLAG_NONE)
    def _set_indoor_unit_op_status(self,uid,op_status_id):
        '''(internal function) set a indoor unit operation status to nocare, heating or cooling'''
        self.logger.debug('_set_indoor_unit_op_status (%s,%s)' % (uid,op_status_id))
        status_values = self.get_indoor_unit_status_information(uid, int_values_mode=True)
        current_value = status_values[1]
        self._set_indoor_unit_value_2(uid, current_value)
        sleep(ADAPTER_SILENT_INTERVAL)
        new_value = (current_value & 0xf0ff) | op_status_id 
        return self._set_indoor_unit_value_2(uid, new_value)
    def set_indoor_unit_op_status_notcare(self,uid):
        '''set a indoor unit operation status to nocare'''
        self.logger.debug('set_indoor_unit_op_status_heating (%s)' % uid)
        return self._set_indoor_unit_op_status(uid, OP_STATUS_ID_DONT_CARE)
    def set_indoor_unit_op_status_heating(self,uid):
        '''set a indoor unit operation status to heating'''
        self.logger.debug('set_indoor_unit_op_status_heating (%s)' % uid)
        return self._set_indoor_unit_op_status(uid, OP_STATUS_ID_HEATING)
    def set_indoor_unit_op_status_cooling(self,uid):
        '''set a indoor unit operation status to cooling'''
        self.logger.debug('set_indoor_unit_op_status_cooling (%s)' % uid)
        return self._set_indoor_unit_op_status(uid, OP_STATUS_ID_COOLING)

    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def _set_indoor_unit_value_3(self,uid,value):
        '''(internal function) write DIII 3rd Register with hex value'''
        try:
            if int(uid) in UID_TOTAL_LIST:
                registeraddress = 42003 + 3*(int(uid) - 100) - HOLDING_REGISTER_ADDRESS_BASE
                self.write_register(registeraddress, value)
                return WRITE_REGISTER_OK_DICT
            else:
                raise Exception('unit id (%s) invalid' % uid)
        except:
            self.logger.error('_set_indoor_unit_value_3 error',exc_info=True)
            raise Exception('_set_indoor_unit_value_3 error')
    def set_indoor_unit_setpoint(self,uid,degreec):
        '''set a indoor unit target temperature'''
        self.logger.debug('set_indoor_unit_setpoint (%s,%s)' % (uid,degreec))
        if float(degreec) < -127.9 or float(degreec) > 127.9:
            raise Exception('param degreec value error')
        status_values = self.get_indoor_unit_status_information(uid, int_values_mode=True)
        current_value = status_values[2]
        self._set_indoor_unit_value_3(uid, current_value)
        sleep(ADAPTER_SILENT_INTERVAL)
        setpoint_value = int(10*float(degreec))
        return self._set_indoor_unit_value_3(uid, setpoint_value)
    
    @retry(stop_max_attempt_number=MAX_RETRY_TIME,wait_fixed=RETRY_DELAY)
    def _set_indoor_unit_compond_values(self,uid,compond_values=[]):
        '''(internal function) write DIII First Register with 3-short list value'''
        try:
            if int(uid) in UID_TOTAL_LIST:
                registeraddress = 42001 + 3*(int(uid) - 100) - HOLDING_REGISTER_ADDRESS_BASE
                import struct
                t_bytes = []
                for ushort in compond_values:
                    s = struct.pack('H',ushort)
                    first, second = struct.unpack('>BB', s)
                    t_bytes.append(first)
                    t_bytes.append(second)
                    
                data_bytes = bytearray(t_bytes)
                reg_str = str(data_bytes)
                self.write_string(
                            registeraddress,
                            reg_str,
                            numberOfRegisters=len(data_bytes)/2
                            )
                return WRITE_REGISTER_OK_DICT
            else:
                raise Exception('unit id (%s) invalid' % uid)
        except:
            self.logger.error('_set_indoor_unit_compond_values error', exc_info=True)
            raise Exception('_set_indoor_unit_compond_values error')
        
        
    def set_indoor_unit_compond(self,uid,mode_code,fan_code,degreec):
        '''set a indoor unit for mode, fan level and target temperature at a time'''
        self.logger.debug('set_indoor_unit_compond (%s,%s,%s,%s)' % (
            uid,mode_code,fan_code,degreec))
        t_values = self.get_indoor_unit_status_information(uid=uid, int_values_mode=True)
        current_values = t_values[:3]

        #-> set power on
        t_values[0] = (t_values[0] & 0xfffe) | 0x0001

        #-> set fan level
        t_values[0] |= FAN_CONTROL_FLAG
        t_values[0] = (t_values[0] & 0x8fff) | FAN_CONTROL_FLAG | (fan_code << 12) 

        #-> set mode
        t_values[1] = (t_values[1] & 0xfff0) | mode_code 

        #-> set target temperature
        t_values[2] = int(10*float(degreec))

        #-> set current value list to VRV
        self._set_indoor_unit_compond_values(uid, current_values)
        sleep(ADAPTER_SILENT_INTERVAL)
        
        #-> set new value list to VRV
        return self._set_indoor_unit_compond_values(uid, t_values[:3])
        
    @classmethod
    def print_class_digest(cls):
        '''list the class-method and object-method information'''
        cls_methods = []
        obj_methods = []
        for func_name in cls.__dict__:
            if func_name.find('_') != 0:
                func = getattr(cls,func_name)
                if type(func) == types.MethodType:
                    if func.__self__: # classmethod
                        cls_methods.append([func_name,func.__doc__])
                    else: # object-method
                        obj_methods.append([func_name,func.__doc__])
        print(json.dumps({'class_methods': cls_methods,
                          'object_methods': obj_methods},indent=2))
        
if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(
        description='Modbus Device Driver Utility')

    parser.add_argument(
        'SERIALPORT',
        nargs='?',
        help="serial port name",
        default='/dev/ttyUSB0')

    parser.add_argument(
        'SLAVE_ADDR',
        type=int,
        nargs='?',
        help="modbus slave address",
        default=0)

    parser.add_argument(
        'BAUDRATE',
        type=int,
        nargs='?',
        help='set baud rate, default: %(default)s',
        default=19200)

    parser.add_argument(
        '--command',
        help='function name as command to be executed,default:%(default)s',
        default='print_class_digest')
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='set logging.level=DEBUG',
        default=False)

    group = parser.add_argument_group('serial port')

    group.add_argument(
        "--bytesize",
        choices=[7, 8],
        help="set byte size, one of {7,8}, default: %(default)s",
        default=8)

    group.add_argument(
        "--stopbits",
        choices=[1, 1.5, 2],
        type=float,
        help="set stopbits, one of {1 1.5 2}, default: %(default)s",
        default=1)

    group.add_argument(
        "--parity",
        choices=['N', 'E', 'O', 'S', 'M'],
        type=lambda c: c.upper(),
        help="set parity, one of {N E O S M}, default: %(default)s",
        default='E')
        
    args = parser.parse_args()

    obj = DaikinD3Net(args=args)
    obj.logger.info('init with class %s' % obj.__class__)
     
    try :
        if args.command:
            obj.logger.debug('command function: %s' % args.command)
            cmd_func = getattr(obj, args.command)
            cmd_func()
            obj.logger.info('command function %s executed' % args.command)
        else:
            parser.print_help()            
    except:
        obj.logger.error('class utility script exception',exc_info=True ) 
    
            
