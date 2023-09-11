from dataclasses import dataclass
from entities.Service import Service


@dataclass
class RESTService(Service):
    SERVICE_TYPE = 'REST'
    service_ip: str

    def to_dict(self) -> dict:
        return {
            'serviceType': self.SERVICE_TYPE,
            'serviceIP': self.service_ip
        }
