#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import sys
import logging
import fileinput
import csv
import re
import daikind3net as daikin
import shutil


def get_mode_code_by_btn_caption(btn_caption):
    if btn_caption.find('暖') == 0:
        return daikin.OP_MODE_ID_HEATING
    elif btn_caption.find('冷') == 0:
        return daikin.OP_MODE_ID_COOLING
    elif btn_caption.find('除濕') == 0:
        return daikin.OP_MODE_ID_DRY
    elif btn_caption.find('送風') == 0:
        return daikin.OP_MODE_ID_FAN
    else:
        logger.warning('unknown btn caption mode text {btn_caption}'.format(
            btn_caption=btn_caption))
        return None

def get_fan_volume_code_by_btn_caption(btn_caption):
    if btn_caption.find('大') > 0:
        return daikin.FAN_VOLUME_ID_HIGHT
    elif btn_caption.find('中') > 0:
        return daikin.FAN_VOLUME_ID_MEDIUM
    elif btn_caption.find('小') > 0:
        return daikin.FAN_VOLUME_ID_LOW
    else:
        logger.warning('unknown btn caption fan volume text {btn_caption}'.format(
            btn_caption=btn_caption))
        return None

def get_int_value_from_text(parse_text):
    matched = re.search(r'\d+', parse_text)
    if matched:
        return int(matched.group())
    else:
        logger.warning('parse_text param no integer value exist {parse_text}'.format(
            parse_text=parse_text))
        return None
    
def main(args,logger):
    ''''''
    filename = os.path.basename(args.cmd_arg_file)
    tmp_file_path = os.path.join(os.path.dirname(args.cmd_arg_file),'%s.tmp' % filename)
    logger.info('tmp_file_path: %s' % tmp_file_path)

    with open(args.cmd_arg_file,'rb') as fh:
        reader = csv.reader(fh, delimiter=',', quotechar="'")
        cmd_arg_list = []
        for row in reader:
            btn_id,btn_caption,cmd_text,arg_text = row
            line = "{btn_id},{btn_caption},'{cmd_text}','{arg_text}'".format(
                btn_id=btn_id,btn_caption=btn_caption,
                cmd_text=cmd_text,arg_text=arg_text)
            new_line = None
            if btn_caption.find('暖') == 0 or btn_caption.find('冷') == 0 or\
                btn_caption.find('除濕') == 0 or btn_caption.find('送風') == 0:
                t_mode = get_mode_code_by_btn_caption(btn_caption)
                t_volume = get_fan_volume_code_by_btn_caption(btn_caption)
                t_value = get_int_value_from_text(btn_caption)
                if btn_caption.find('暖') == 0 or btn_caption.find('冷') == 0:
                    arg_text = '%s,%s,%s' % (t_mode,t_volume,t_value)
                    t_cmd = 'set_indoor_unit_compond'
                else:
                    arg_text = '%s,%s' % (t_mode,t_volume)
                    t_cmd = 'set_indoor_unit_compond'
            elif btn_caption.lower().find('on') == 0 or btn_caption.lower().find('off') == 0:
                arg_text = ''
                t_cmd = 'on' if btn_caption.lower().find('on') == 0 else 'off'
            else:
                arg_text = None
                t_cmd = None
                logger.warning('unknown btn caption %s' % btn_caption)
        
            new_line = "{btn_id},{btn_caption},'{cmd_text}','{arg_text}'".format(
                btn_id=btn_id,btn_caption=btn_caption,
                cmd_text=t_cmd,arg_text=arg_text)
            if line != new_line:
                logger.info('line [%s] updated: [%s]' % (line,new_line))
            else:
                logger.debug('line [%s] remain not change' % (line))
            cmd_arg_list.append(new_line)
            
    with open(tmp_file_path,'wb') as fh:
        fh.write('\n'.join(cmd_arg_list))
    
    shutil.move(tmp_file_path, args.cmd_arg_file)
    logger.info('== done ==')

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
        'cmd_arg_file',
        help='existing file to be process',
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
    
    try :
        logger.info('args: %s' % str(args))
        if not os.path.exists(args.cmd_arg_file):
            parser.print_help()
            sys.exit(2)
        else:
            main(args=args,logger=logger)
    except:
        logger.error('error',exc_info=True ) 
        
        
        
        

