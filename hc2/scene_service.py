
import os
import shutil
import codecs
import json

from .base_service import HC2BaseService
from .api_scene import HC2APIScene


class HC2SceneService(HC2BaseService):

    def __init__(self, args=None, logger=None):
        super(HC2SceneService,self).__init__(args,logger)

    def _get_scene_dump_path(self, scene_id, del_exist=False):
        """create dump folder (./.dump/hostname/scenes/scene_id) if not exist"""

        dump_path = os.path.join(
            self._get_dump_root(), 'scenes', str(scene_id))
        if os.path.exists(dump_path):
            if del_exist:
                shutil.rmtree(dump_path)
                os.makedirs(dump_path)
        else:
            os.makedirs(dump_path)
        return dump_path

    # -- dump_scene
    @staticmethod
    def _get_scene_json_dump_filename(scene):
        return '{id}.{name}.json'.format(id=scene['id'], name=scene['name'].encode('utf8')).decode('utf8')

    @staticmethod
    def _get_scene_lua_code_filename(scene):
        return '{id}.{name}.lua'.format(id=scene['id'], name=scene['name'].encode('utf8')).decode('utf8')

    def _dump_scene(self, dump_path, scene):
        """
        save hc2 scene json file ({scene_id}.{scene_name}.json)
        and lua code:
            {scene_id}.{scene_name}.lua
        """

        # dump json
        filename = self._get_scene_json_dump_filename(scene)
        with codecs.open(os.path.join(dump_path, filename), 'wb', encoding='utf8') as fh:
            fh.write(json.dumps(scene, indent=2))
        self.logger.debug('... scene %s (%s) json dumped' % (scene['id'], scene['name']))

        # dump scene lua code
        lua_code = scene['lua']
        lua_code = lua_code.encode('utf-8').replace('\\n', '\n')
        filename = self._get_scene_lua_code_filename(scene)
        with codecs.open(os.path.join(dump_path, filename), 'wb', encoding='utf8') as fh:
            fh.write(lua_code.decode('utf8'))
        self.logger.debug('... scene lua code dumped %s' % filename)

    def dump_scene(self, scene_id):
        """get hc2 scene json object via HTTP API and save as local files"""

        self.logger.debug('dump_scene %s' % scene_id)

        hc2_scene_api = HC2APIScene(self.args, self.logger)
        scene = hc2_scene_api.get(key=scene_id)
        if scene:
            dump_path = self._get_scene_dump_path(scene_id, True)
            self._dump_scene(dump_path, scene)
            self.logger.debug('... dump_scene [%s] completed' % scene['name'])
            self.logger.debug('... dump path %s' % dump_path)
        else:
            self.logger.warning('dump_scene with id %s result None' % scene_id)

        return scene

    # --- update_scene
    def update_scene(self, scene_id):
        """update hc2 scene with local dumped files
        and the origin scene json object will be backup"""

        self.logger.debug('update_scene %s with local dump files' % scene_id)

        # check scene exist in hc2
        hc2_scene_api = HC2APIScene(self.args, self.logger)
        scene = hc2_scene_api.get(key=scene_id)

        if scene is None:
            self.logger.warning('fail to get scene (id %s) json from hc2, exit' % scene_id)
            return None

        # load local scene json
        dump_path = self._get_scene_dump_path(scene_id)
        filename = self._get_scene_json_dump_filename(scene)
        if not os.path.exists(os.path.join(dump_path, filename)):
            self.logger.warning('scene id %s dump file (%s) not exist' % (scene_id, filename))
            return None
        with open(os.path.join(dump_path, filename)) as fh:
            t_scene = json.loads(fh.read())

        # update scene properties attr. lua
        filename = self._get_scene_lua_code_filename(scene)
        file_path = os.path.join(dump_path, filename)
        if os.path.exists(file_path):
            with open(file_path) as fh:
                lua_code = fh.read()
                # mainloop = mainloop.replace('\n','\\n')
                scene['lua'] = lua_code
                self.logger.debug('... scene properties lua updated')
        else:
            self.logger.warning('scene %s lua code dump file (%s) not exist' % (
                scene_id, file_path))

        # update scene attr. name
        if scene['name'] != t_scene['name']:
            scene['name'] = t_scene['name']
            self.logger.debug('... update scene name as %s' % (
                scene['name'].encode('utf8')))

        # update scene on hc2
        scene = hc2_scene_api.put(scene['id'], scene)

        if scene:
            self.logger.debug('hc2 scene (%s:%s) update completed' % (
                scene['id'], scene['name'].encode('utf8')))
        else:
            self.logger.warning('hc2 scene (%s:%s) put api fail' % (
                t_scene['id'], t_scene['name'].encode('utf8')))

        self.logger.debug('... update_scene completed')

        return scene

    # -- get_scenes
    def get_scenes(self):
        """return hc2 /api/scenes"""

        import api_scene
        hc2_scene_api = api_scene.HC2APIScene(self.args, self.logger)
        t_scenes = hc2_scene_api.get(key=None)
        if t_scenes is None:
            self.logger.warning('hc2 scenes api for all scenes call fail')

        return t_scenes

    # -- start_scene
    def start_scene(self, scene_id):
        """return hc2 /api/sceneControl"""

        import api_scene
        hc2_scene_api = api_scene.HC2APIScene(self.args, self.logger)
        t_result = hc2_scene_api.start_scene(scene_id=scene_id)

        return t_result


if __name__ == '__main__':
    HC2SceneService.main()
