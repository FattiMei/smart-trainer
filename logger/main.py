import time
import asyncio
import argparse
from devscan import scan_for_devices


DEFAULT_WINDOW_SIZE_SECONDS = 15.0


def parse_window_parameters(default_window_size_seconds: float = DEFAULT_WINDOW_SIZE_SECONDS):
    parser = argparse.ArgumentParser(
        prog='logger',
        description='Collects and visualize data from UWB radar and Arduino boards'
    )

    arguments = [
        ('-group'      , str  , 'Group name'                                     ),
        ('-subject'    , str  , 'Subject name'                                   ),
        ('-activity'   , str  , 'Activity name'                                  ),
        ('-info'       , str  , 'Additional information'                         ),
        ('-window_size', float, 'Collection window size in seconds'              ),
        ('-delay'      , float, 'Delay in seconds before starting the collection'),
    ]

    for (name, type, help) in arguments:
        parser.add_argument(name, type=type, help=help)

    args = parser.parse_args()

    if args.window_size is None:
        args.window_size = default_window_size_seconds

    return args


async def main():
    window_parameters = parse_window_parameters()
    available_devices = await scan_for_devices()

    if available_devices == []:
        print('No compatible device found')
        exit()

    print('Devices found:')
    for device in available_devices:
        print(f'  * {device.name} at {device.port}')


if __name__ == '__main__':
    asyncio.run(main())
