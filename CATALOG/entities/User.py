from dataclasses import dataclass


@dataclass
class User(object):
    user_id: int
    chat_id: int
    aquariums: list[int]

    def to_dict(self) -> dict:
        return {
            'userID': self.user_id,
            'chatID': self.chat_id,
            'aquariums': self.aquariums,
        }
