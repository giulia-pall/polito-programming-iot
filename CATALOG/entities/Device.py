from dataclasses import dataclass
from entities.Service import Service


@dataclass
class Device(object):
    device_id: int
    device_name: str
    measure_type: list[str]
    available_services: list[str]
    services_details: list[Service]
    last_update: str
    connected_to: str
    port: str

    @staticmethod
    def get_fields_map() -> dict:
        return {
            'deviceID': 'device_id',
            'deviceName': 'device_name',
            'measureType': 'measure_type',
            'availableServices': 'available_services',
            'servicesDetails': 'services_details',
            'lastUpdate': 'last_update',
            'connectedTo': 'connected_to',
            'port': 'port'
        }

    def get_services_details(self) -> list[dict]:
        services = []

        for service in self.services_details:
            services.append(service.to_dict())
        return services

    def to_dict(self) -> dict:
        return {
            'deviceID': self.device_id,
            'deviceName': self.device_name,
            'measureType': self.measure_type,
            'availableServices': self.available_services,
            'servicesDetails': self.get_services_details(),
            'lastUpdate': self.last_update,
            'connectedTo': self.connected_to,
            'port': self.port
        }
