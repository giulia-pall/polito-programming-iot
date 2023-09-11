from dataclasses import dataclass


@dataclass
class Topic(object):
    topic: str
    type: str

    def to_dict(self) -> dict:
        return {
            'topic': self.topic,
            'type': self.type
        }
