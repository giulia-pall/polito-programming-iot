from datetime import datetime

import cherrypy

from entities.Catalog import Catalog


class WebServer(object):
    """CherryPy webserver."""
    exposed = True

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        """Define the GET API."""
        if len(uri) < 1:
            return {
                'status': 'error',
                'description': 'Missing parameter(s).'
            }
        catalog = Catalog('device_registry.json', 'service_registry.json')
        if uri[0] == 'resource':
            catalog.load_resource_registry_from_file()
            return catalog.resource_registry
        elif uri[0] == 'service':
            catalog.load_service_registry_from_file()
            return catalog.service_registry
        return {
            'status': 'error',
            'description': 'Unknown registry.'
        }

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        """Define the POST API."""
        json_params = cherrypy.request.json
        if len(uri) < 1:
            return {
                'status': 'error',
                'description': 'Missing parameter(s).'
            }
        catalog = Catalog('device_registry.json', 'service_registry.json')
        catalog.load_resource_registry_from_file()
        catalog.load_service_registry_from_file()

        entity = uri[0]

        if entity == 'device':
            try:
                if catalog.get_device_by_id(json_params['deviceID']):
                    return {
                        'status': 'error',
                        'description': 'You cannot overwrite existing device.'
                    }
                catalog.add_device(Catalog.parse_device(json_params))
            except KeyError:
                return {
                    'status': 'error',
                    'description': 'Missing Key'
                }
        elif entity == 'aquarium':
            try:
                aquarium_devices = catalog.generate_aquarium_devices(json_params['aquariumID'])
                devices_ids = [int(device.device_id) for device in aquarium_devices]
                json_params['devicesList'] = devices_ids
                catalog.add_aquarium(Catalog.parse_aquarium(json_params))
                for device in aquarium_devices:
                    catalog.add_device(device)
            except KeyError:
                return {
                    'status': 'error',
                    'description': 'Missing Key'
                }
        elif entity == 'user':
            try:
                if catalog.get_user_by_chat_id(json_params['chatID']):
                    return {
                        'status': 'error',
                        'description': f"The user with chatID {json_params['chatID']} already exists."
                    }
                for aquarium_id in json_params['aquariums']:
                    if not catalog.get_aquarium_by_id(aquarium_id):
                        return {
                            'status': 'error',
                            'description': f"The aquarium with ID {aquarium_id} does not exist."
                        }
                catalog.add_user(Catalog.parse_user(json_params))
            except KeyError:
                return {
                    'status': 'error',
                    'description': 'Missing Key'
                }
        elif entity == 'controller':
            try:
                if catalog.get_controller_by_id(json_params['controllerID']):
                    return {
                        'status': 'error',
                        'description': 'You cannot overwrite existing device.'
                    }
                catalog.add_controller(Catalog.parse_controller(json_params))
            except KeyError:
                return {
                    'status': 'error',
                    'description': 'Missing Key'
                }
        else:
            return {
                'status': 'error',
                'description': 'Unknown URI: ' + entity
            }
        catalog.save_resource_registry_to_file()
        catalog.save_service_registry_to_file()
        return {'status': 'success'}

    @cherrypy.tools.json_out()
    def DELETE(self, *uri, **params):
        """Define the DELETE API."""
        if len(uri) < 2:
            return {
                'status': 'error',
                'description': 'Missing parameter(s).'
            }
        catalog = Catalog('device_registry.json', 'service_registry.json')
        catalog.load_resource_registry_from_file()
        catalog.load_service_registry_from_file()

        entity = uri[0]
        entity_id = int(uri[1])

        if entity == 'device':
            if not catalog.get_device_by_id(entity_id):
                return {
                    'status': 'error',
                    'description': f"Device with ID {entity_id} does not exist."
                }
            catalog.remove_device(entity_id)
        elif entity == 'aquarium':
            if not catalog.get_aquarium_by_id(entity_id):
                return {
                    'status': 'error',
                    'description': f"Aquarium with ID {entity_id} does not exist."
                }
            catalog.remove_aquarium(entity_id)
        elif entity == 'user':
            if not catalog.get_user_by_id(entity_id):
                return {
                    'status': 'error',
                    'description': f"User with ID {entity_id} does not exist."
                }
            catalog.remove_user(entity_id)
        elif entity == 'controller':
            if not catalog.get_controller_by_id(entity_id):
                return {
                    'status': 'error',
                    'description': f"Controller with ID {entity_id} does not exist."
                }
            catalog.remove_controller(entity_id)
        else:
            return {
                'status': 'error',
                'description': 'Unknown URI: ' + entity
            }
        catalog.save_resource_registry_to_file()
        catalog.save_service_registry_to_file()
        return {'status': 'success'}


def main():
    cherrypy.tree.mount(WebServer(), '/', config='cherrypy.conf')
    cherrypy.config.update('cherrypy.conf')
    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == '__main__':
    main()
