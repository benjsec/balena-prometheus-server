import argparse
import asyncio
import json
import logging
import logging.config
import os
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from balena import Balena


logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '[%(asctime)s %(name)-8s] %(levelname)-1s %(message)s'}
        },
    handlers = {
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.INFO}
        },
    root = {
        'handlers': ['h'],
        'level': logging.INFO,
        },
)

logging.config.dictConfig(logging_config)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
log = logging.getLogger()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--api-token', default=os.environ.get('BALENA_API_TOKEN'))
    parser.add_argument('--app-name', default=os.environ.get('BALENA_APP_NAME'))
    parser.add_argument('-o', '--outfile', default='./targets.json')
    return parser.parse_args()


def format_device(device):
    return {
        'targets': [device['uuid'] + ".resindevice.io:80"],
        'labels': {
            'resin_device_uuid': device['uuid'],
            'resin_app': device['application'][0]['app_name']
        }
    }


async def generate_json(args):
    balena = Balena()
    if not args.api_token:
        raise SystemExit('BALENA_API_TOKEN environment variable not set.')

    app_name = args.app_name
    if not app_name:
        raise SystemExit('BALENA_APP_NAME environment variable not set.')
    
    balena.auth.login_with_token(args.api_token)
    if not balena.auth.is_logged_in():
        log.error('Authentication failure.')
        return
    log.debug("Logged in.")

    devices = balena.models.device.get_all_by_application(args.app_name)

    if devices:
        with open(args.outfile, 'w') as f:
            json.dumps([format_device(dev) for dev in devices], f)
    else:
        log.error("No devices found")


if __name__ == '__main__':
    args = parse_args()
    if args.verbose:
        log.setLevel(logging.DEBUG)
        logging.getLogger('apscheduler').setLevel(logging.DEBUG)

    interval = os.environ.get('DISCOVERY_INTERVAL', 10)
    log.info("Will update device list every %ss", interval)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_json, args=[args], trigger='interval', seconds=interval)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
