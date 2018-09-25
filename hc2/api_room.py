#!/usr/bin/env python

from api_base import HC2APIBase


class HC2APIRoom(HC2APIBase):

    def __init__(self, args=None, logger=None):
        super(HC2APIRoom, self).__init__(args, logger)
        self.api_url = self.api_root_url + '/rooms'
        self.logger.debug('api_url: %s' % self.api_url)


if __name__ == '__main__':
    HC2APIRoom.main()
