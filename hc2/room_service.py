
from .base_service import HC2BaseService
from .api_room import HC2APIRoom


class HC2RoomService(HC2BaseService):

    def __init__(self, args=None, logger=None):
        super(HC2RoomService,self).__init__(args,logger)

    def get_rooms(self):
        """return hc2 /api/rooms"""

        hc2_room_api = HC2APIRoom(self.args, self.logger)
        t_rooms = hc2_room_api.get(key=None)
        if t_rooms is None:
            self.logger.warning('hc2 rooms api for all rooms call fail')

        return t_rooms


if __name__ == '__main__':
    HC2RoomService.main()
