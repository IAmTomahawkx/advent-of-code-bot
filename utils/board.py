import datetime
from discord import utils

from . import tz

class Member:
    __slots__ = "global_score", "id", "stars", "local_score", "last_star", "completion_stats", "name"
    def __init__(self, value):
        self.global_score = value['global_score']
        self.id = int(value['id'])
        self.name = value['name']
        self.local_score = value['local_score']
        self.stars = value['stars']
        self.last_star = datetime.datetime.fromtimestamp(int(value['last_star_ts']), tz=tz.EST5EDT()) if value['last_star_ts'] else None
        self.completion_stats = {
            int(a): {
                1: datetime.datetime.fromtimestamp(int(b['1']['get_star_ts']), tz=tz.EST5EDT()) if b.get('1', None) is not None else None,
                2: datetime.datetime.fromtimestamp(int(b['2']['get_star_ts']), tz=tz.EST5EDT()) if b.get('2', None) is not None else None,
            } for a, b in value['completion_day_level'].items()
        }


class Board:
    __slots__ = "owner", "owner_id", "event", "members", "fetched"
    def __init__(self, data):
        self.owner_id = int(data['owner_id'])
        self.event = data['event']
        self.members = [Member(m) for m in data['members'].values()]
        self.owner = utils.get(self.members, id=self.owner_id)
        self.fetched = datetime.datetime.utcnow()

    @property
    def sort_by_local_board(self):
        v = self.members.copy()
        v.sort(key=lambda m: m.local_score, reverse=True)
        return v

    @property
    def sort_by_global_board(self):
        v =self.members.copy()
        v.sort(key=lambda m: m.global_score, reverse=True)
        return v

    @property
    def latest_star(self):
        return max(self.members, key=lambda m: m.last_star.timestamp() if m.last_star else -1)
