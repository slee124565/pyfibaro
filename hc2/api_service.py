#!/usr/bin/env python

import requests
import json

from api_base import HC2APIBase


class HC2APIService(HC2APIBase):

    def __init__(self, args=None, logger=None):
        super(HC2APIService, self).__init__(args, logger)
        self.api_url = self.api_root_url + '/service'
        self.logger.debug('api_url: %s' % self.api_url)

    def reboot(self):

        try:
            api_url = self.api_url + '/reboot'

            r = requests.post(
                api_url,
                data=json.dumps({'data':'reset'}),
                auth=requests.auth.HTTPBasicAuth(self.username, self.password))

            if r.status_code in range(200, 300):
                data = r.content
                self.logger.debug('api data type %s' % type(data))
                return data
            else:
                msg = 'hc2 post api ({api_url}) call fail with requests status code {status_code}'.format(
                    api_url=api_url, status_code=r.status_code)
                self.logger.warning(msg)
                self.logger.debug('requests.post fail response content:\n%s' % r.content)
                return None
        except:
            self.logger.error('{cls.__name__} post func exception'.format(cls=self.__class__), exc_info=True)
            return None

    # @staticmethod
    # def get_dev_api_service(service):
    #     return HC2APIService(service.args, service.logger)


if __name__ == '__main__':
    HC2APIService.main()
