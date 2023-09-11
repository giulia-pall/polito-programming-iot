from dataclasses import dataclass


@dataclass
class Aquarium(object):
    aquarium_id: int
    devices_list: list[int]
    chat_id: list[int]
    feed_time: str
    feed_schedule: int
    changed: bool

    def to_dict(self) -> dict:
        return {
            'aquariumID': self.aquarium_id,
            'devicesList': self.devices_list,
            'chatID': self.chat_id,
            'feedTime': self.feed_time,
            'feedSchedule': self.feed_schedule,
            'changed': self.changed
        }
