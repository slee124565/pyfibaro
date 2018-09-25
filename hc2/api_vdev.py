#!/usr/bin/env python
"""
"""

from api_base import HC2APIBase


class HC2APIVirtualDevice(HC2APIBase):

    def __init__(self, args=None, logger=None):
        super(HC2APIVirtualDevice,self).__init__(args, logger)
        self.api_url = self.api_root_url + '/virtualDevices'
        self.logger.debug('api_url: %s' % self.api_url)
        
    def post(self,src_dev):
        """Implement HC2 HTTP POST API"""

        # keep dev json keys ['name','type','actions','properties'] member only
        t_dev = dict(src_dev)  # keep original dev json obj
        for key in t_dev.keys():
            if key not in ['name', 'type', 'actions', 'properties']:
                t_dev.pop(key, None)
                
        return super(HC2APIVirtualDevice, self).post(t_dev)

    # @staticmethod
    # def get_dev_api_service(service):
    #     return HC2APIVirtualDevice(service.args,service.logger)
    
    
if __name__ == '__main__':
    HC2APIVirtualDevice.main()
