#!/usr/bin/env python
'''
'''

from api_base import HC2APIBase

class HC2APIGlobalVariable(HC2APIBase):
    
    
    def __init__(self,args=None,logger=None):
        super(HC2APIGlobalVariable,self).__init__(args, logger)
        self.api_url = self.api_root_url + '/globalVariables'
        self.logger.debug('api_url: %s' % self.api_url)
    
#     def post(self, obj):
#         raise Exception('hc2 globalVariables api not support HTTP post')
            
    # @staticmethod
    # def get_dev_api_service(service):
    #     return HC2APIGlobalVariable(service.args,service.logger)
    
    
if __name__ == '__main__':
    HC2APIGlobalVariable.main()