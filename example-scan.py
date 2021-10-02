import json
from time import sleep
import uuid
from warnings import filterwarnings

import requests

filterwarnings('ignore', message='Unverified HTTPS request')
host = 'https://127.0.0.1:8834'
proxies = None
with open('/opt/nessus/var/nessus/config.json') as config_file:
    config = json.load(config_file)


def scan(template_name, targets):
    # Create a session
    # /api#/resources/session/create
    response = requests.post(
        host + '/session',
        json={'username': config['user']['username'], 'password': config['user']['password']},
        verify=False,
        proxies=proxies
    )
    headers = {'X-Cookie': 'token=' + response.json()['token']}

    # Get scan template uuid
    # /api#/resources/editor/list
    response = requests.get(
        host + '/editor/scan/templates',
        headers=headers,
        verify=False,
        proxies=proxies
    )
    for template in response.json()['templates']:
        if template['name'] == template_name:
            template_uuid = template['uuid']

    # Create a unique scan name
    name = template_name + '.' + str(uuid.uuid4().hex)

    # Create the scan
    # /api#/resources/scans/create
    response = requests.post(
        host + '/scans',
        headers=headers,
        json={
            'uuid': template_uuid,
            'settings': {
                'name': name,
                'enabled': False,
                'text_targets': targets,
                'ping_the_remote_host': 'yes',
                'fast_network_discovery': 'yes'
            },
        },
        verify=False,
        proxies=proxies
    )
    scan_id = response.json()['scan']['id']

    # Launch the scan
    # /api#/resources/scans/launch
    requests.post(
        host + '/scans/' + str(scan_id) + '/launch',
        headers=headers,
        verify=False,
        proxies=proxies
    )

    # Poll scan status until completion
    # /api#/resources/scans/details
    while True:
        response = requests.get(
            host + '/scans/' + str(scan_id),
            headers=headers,
            verify=False,
            proxies=proxies
        )
        scan_status = response.json()['info']['status']
        if scan_status == 'completed':
            break
        elif scan_status == 'aborted':
            quit()
        elif scan_status == 'running':
            sleep(10)

    # Scan data export request
    # /api#/resources/scans/export-request
    response = requests.post(
        host + '/scans/' + str(scan_id) + '/export',
        headers=headers,
        json={
            'format': 'csv'
        },
        verify=False,
        proxies=proxies
    )
    export_token = response.json()['token']

    # Poll export token until completion
    # /api#/resources/tokens/status
    while True:
        response = requests.get(
            host + '/tokens/' + export_token + '/status',
            headers=headers,
            verify=False,
            proxies=proxies
        )
        export_status = response.json()['status']
        if export_status == 'ready':
            break
        elif export_status == 'running':
            sleep(10)

    # Download scan data
    # /api#/resources/tokens/download
    response = requests.get(
        host + '/tokens/' + export_token + '/download',
        headers=headers,
        verify=False,
        proxies=proxies
    )
    with open('/tmp/' + name + '.csv', 'wb') as scan_results_file:
        scan_results_file.write(response.content)

    # Clean up scans
    # /api#/resources/scans/delete
    requests.delete(
        host + '/scans/' + str(scan_id),
        headers=headers,
        verify=False,
        proxies=proxies
    )

    # Destroy session
    # /api#/resources/session/destroy
    requests.delete(
        host + '/session',
        headers=headers,
        verify=False,
        proxies=proxies
    )


scan('discovery', '127.0.0.1')
