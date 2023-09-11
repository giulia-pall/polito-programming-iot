from typing import Optional

from entities.Aquarium import Aquarium
from entities.Controller import Controller
from entities.Device import Device
import json
from datetime import datetime
from copy import deepcopy

from entities.MQTTService import MQTTService
from entities.RESTService import RESTService
from entities.Topic import Topic
from entities.User import User


class Catalog(object):
    def __init__(self, resource_registry_path: str, service_registry_path: str):
        self.resource_registry_path = resource_registry_path
        self.service_registry_path = service_registry_path
        self.resource_registry = None
        self.service_registry = None

    @staticmethod
    def parse_device(device_json: dict) -> Device:
        services = []

        for service_details in device_json['servicesDetails']:
            if service_details['serviceType'] == 'MQTT':
                topics = [Topic(topic['topic'], topic['type']) for topic in service_details['topics']]
                services.append(
                    MQTTService(topics)
                )
            elif service_details['serviceType'] == 'REST':
                services.append(
                    RESTService(service_details['serviceIP'])
                )

        return Device(
            device_json['deviceID'],
            device_json['deviceName'],
            device_json['measureType'],
            device_json['availableServices'],
            services,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            device_json['connectedTo'],
            device_json['port']
        )

    @staticmethod
    def parse_aquarium(aquarium_json: dict) -> Aquarium:
        return Aquarium(
            aquarium_json['aquariumID'],
            aquarium_json['devicesList'],
            aquarium_json['chatID'],
            aquarium_json['feedTime'],
            aquarium_json['feedSchedule'],
            aquarium_json['changed']
        )

    @staticmethod
    def parse_user(user_json: dict) -> User:
        return User(
            user_json['userID'],
            user_json['chatID'],
            user_json['aquariums']
        )

    @staticmethod
    def parse_controller(controller_json: dict) -> Controller:
        topics = [Topic(topic['topic'], topic['type']) for topic in controller_json['topics']]

        return Controller(
            controller_json['controllerID'],
            controller_json['aquariumID'],
            controller_json['name'],
            topics
        )

    def load_resource_registry_from_file(self) -> None:
        with open(self.resource_registry_path, 'r') as registry_file:
            self.resource_registry = json.load(registry_file)

    def load_service_registry_from_file(self) -> None:
        with open(self.service_registry_path, 'r') as registry_file:
            self.service_registry = json.load(registry_file)

    def save_resource_registry_to_file(self) -> None:
        if not self.resource_registry:
            return
        with open(self.resource_registry_path, 'w') as registry_file:
            json.dump(self.resource_registry, registry_file)

    def save_service_registry_to_file(self) -> None:
        if not self.service_registry:
            return
        with open(self.service_registry_path, 'w') as registry_file:
            json.dump(self.service_registry, registry_file)

    def add_device(self, device: Device) -> None:
        if 'devicesList' not in self.resource_registry:
            self.resource_registry['devicesList'] = []
        if not self.get_device_by_id(device.device_id):
            self.resource_registry['devicesList'][str(device.device_id)] = device.to_dict()
            self.update_resource_last_updated()

    def remove_device(self, device_id: int) -> None:
        if self.get_device_by_id(device_id):
            del self.resource_registry['devicesList'][str(device_id)]
            for aquarium_id in self.service_registry['aquariumList']:
                # Remove the device from the aquariums
                if device_id in self.get_aquarium_by_id(aquarium_id).devices_list:
                    self.service_registry['aquariumList'][str(aquarium_id)]['devicesList'].remove(device_id)
            self.update_resource_last_updated()

    def get_device_by_id(self, device_id: int) -> Optional[Device]:
        if 'devicesList' not in self.resource_registry:
            return None
        return self.parse_device(self.resource_registry['devicesList'][str(device_id)]) \
            if str(device_id) in self.resource_registry['devicesList'] else None

    def get_devices_ids(self) -> list[int]:
        if 'devicesList' not in self.resource_registry:
            return []
        return [int(device_id) for device_id in self.resource_registry['devicesList']]

    def get_default_devices(self) -> list[dict]:
        default_devices = []
        if 'defaultDevicesList' not in self.resource_registry:
            return default_devices

        # Make a copy, don't return the original object!
        for default_device_json in self.resource_registry['defaultDevicesList']:
            default_devices.append(deepcopy(default_device_json))
        return default_devices

    def generate_aquarium_devices(self, aquarium_id: int) -> list[Device]:
        current_max_id = max(self.get_devices_ids())
        devices = []
        for device_json in self.get_default_devices():
            device_json['deviceID'] = current_max_id + 1
            current_max_id += 1
            for servicesDetail in device_json['servicesDetails']:
                if 'topics' in servicesDetail:
                    for topic in servicesDetail['topics']:
                        if '{aquarium_id}' in topic['topic']:
                            topic['topic'] = topic['topic'].replace('{aquarium_id}', str(aquarium_id))
            device = self.parse_device(device_json)
            devices.append(device)
        return devices

    def add_aquarium(self, aquarium: Aquarium) -> None:
        if 'aquariumList' not in self.service_registry:
            self.service_registry['aquariumList'] = []
        self.service_registry['aquariumList'][str(aquarium.aquarium_id)] = aquarium.to_dict()
        self.update_service_last_updated()

    def remove_aquarium(self, aquarium_id: int) -> None:
        if self.get_aquarium_by_id(aquarium_id):
            del self.service_registry['aquariumList'][str(aquarium_id)]
            for user_id in self.service_registry['usersList']:
                # Remove the aquarium from the users
                if aquarium_id in self.get_user_by_id(user_id).aquariums:
                    self.service_registry['usersList'][str(user_id)]['aquariums'].remove(aquarium_id)
            self.update_service_last_updated()

    def get_aquarium_by_id(self, aquarium_id: int) -> Optional[Aquarium]:
        if 'aquariumList' not in self.service_registry:
            return None
        return self.parse_aquarium(self.service_registry['aquariumList'][str(aquarium_id)]) \
            if str(aquarium_id) in self.service_registry['aquariumList'] else None

    def add_user(self, user: User) -> None:
        if 'usersList' not in self.service_registry:
            self.service_registry['usersList'] = []
        self.service_registry['usersList'][str(user.user_id)] = user.to_dict()
        self.update_service_last_updated()

    def remove_user(self, user_id: int) -> None:
        if self.get_user_by_id(user_id):
            del self.service_registry['usersList'][str(user_id)]
            self.update_service_last_updated()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        if 'usersList' not in self.service_registry:
            return None
        return self.parse_user(self.service_registry['usersList'][str(user_id)]) \
            if str(user_id) in self.service_registry['usersList'] else None

    def get_user_by_chat_id(self, chat_id: int) -> Optional[User]:
        if 'usersList' not in self.service_registry:
            return None
        for user_id in self.service_registry['usersList']:
            if self.service_registry['usersList'][user_id]['chatID'] == chat_id:
                return self.parse_user(self.service_registry['usersList'][user_id])
        return None

    def add_controller(self, controller: Controller) -> None:
        if 'controllersList' not in self.service_registry:
            self.service_registry['controllersList'] = {}
        self.service_registry['controllersList'][str(controller.controllerID)] = controller.to_dict()
        self.update_service_last_updated()

    def remove_controller(self, controller_id: int) -> None:
        if self.get_controller_by_id(controller_id):
            del self.service_registry['controllersList'][str(controller_id)]
            self.update_service_last_updated()

    def get_controller_by_id(self, controller_id: int) -> Optional[Controller]:
        if 'controllersList' not in self.service_registry:
            return None
        return self.parse_controller(self.service_registry['controllersList'][str(controller_id)]) \
            if (str(controller_id) in self.service_registry['controllersList']) else None

    def update_resource_last_updated(self):
        self.resource_registry['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_service_last_updated(self):
        self.service_registry['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
