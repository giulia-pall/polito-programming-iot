from dataclasses import dataclass

from entities.Topic import Topic


@dataclass
class Controller(object):
    controllerID: int
    aquarium_id: int
    name: str
    topics: list[Topic]

    def get_topics(self) -> list[dict]:
        topics = []

        for topic in self.topics:
            topics.append(topic.to_dict())
        return topics

    def to_dict(self) -> dict:
        return {
            'controllerID': self.controllerID,
            'aquariumID': self.aquarium_id,
            'name': self.name,
            'topics': self.get_topics()
        }
