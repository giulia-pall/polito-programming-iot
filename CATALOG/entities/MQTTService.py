from dataclasses import dataclass

from entities.Topic import Topic
from entities.Service import Service


@dataclass
class MQTTService(Service):
    SERVICE_TYPE = 'MQTT'
    topics: list[Topic]

    def get_topics(self) -> list[dict]:
        topics = []

        for topic in self.topics:
            topics.append(topic.to_dict())
        return topics

    def to_dict(self) -> dict:
        return {
            'serviceType': self.SERVICE_TYPE,
            'topics': self.get_topics(),
        }
