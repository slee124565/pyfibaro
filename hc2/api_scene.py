#!/usr/bin/env python

from api_base import HC2APIBase


class HC2APIScene(HC2APIBase):

    def __init__(self, args=None, logger=None):
        super(HC2APIScene,self).__init__(args, logger)
        self.api_url = self.api_root_url + '/scenes'
        self.logger.debug('api_url: %s' % self.api_url)
        
    def put(self, key, obj):
        if self.put(self, key, obj):
            return self.get(key)
        else:
            return None

    def _scene_control(self, scene_id, action='start'):

        import requests

        api_url = self.api_root_url + '/sceneControl'
        params = {'id': scene_id, 'action': 'start'}

        r = requests.get(api_url,
                         params=params,
                         auth=requests.auth.HTTPBasicAuth(
                             self.username,
                             self.password))

        if r.status_code in range(200,300):
            return True
        else:
            msg = 'hc2 get api ({api_url}) call fail with requests status code {status_code}'.format(
                api_url=api_url, status_code=r.status_code)
            self.logger.warning(msg)
            self.logger.debug('requests.get fail response content:\n%s' % (r.content))
            return False

    def start_scene(self, scene_id):
        return self._scene_control(scene_id)

    def stop_scene(self, scene_id):
        return self._scene_control(scene_id, 'stop')


if __name__ == '__main__':
    HC2APIScene.main()
