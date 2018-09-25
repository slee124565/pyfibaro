#!/usr/bin/env python
'''
'''

from api_base import HC2APIBase

class HC2APIDevice(HC2APIBase):
    
    
    def __init__(self,args=None,logger=None):
        super(HC2APIDevice,self).__init__(args, logger)
        self.api_url = self.api_root_url + '/devices'
        self.logger.debug('api_url: %s' % self.api_url)
        
    # @staticmethod
    # def get_dev_api_service(service):
    #     return HC2APIDevice(service.args,service.logger)
    
    
if __name__ == '__main__':
    HC2APIDevice.main()
