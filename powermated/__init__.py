from evdev import InputDevice, ecodes, list_devices
import sys
import errno
import logging
import pulsectl
from logging import DEBUG

KEY_PRESS = 1
INCREASE = 1
INCREASE_AMOUNT = 0.02
DECREASE_AMOUNT = -0.02

log = logging.getLogger('powermated')
log.setLevel(DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))


def find_device():
    """
    Search for the device representing the interface to the Griffin Powermate.

    :return: A list containing the devices found, empty if no matching device is found.
    """
    log.info('Searching for Griffin Powermate input device')
    devices = [InputDevice(fn) for fn in list_devices()]
    for device in devices:
        if device.name.find('PowerMate') != -1:
            log.info('Device found: %s (%s)', device.name, device.phys)
            return [device.fn]
    return []


def listen_on(device):
    """
    Monitor the given device and modify the sound volume

    :param device: the name of the device to read
    """

    log.info('Listening on %s', device)

    try:
        with pulsectl.Pulse('Griffin Powermate') as pulse:

            for event in InputDevice(device).read_loop():

                # ignore synchronization events
                if event.type == ecodes.EV_SYN:
                    continue

                # event action: toggle mute
                if event.type == ecodes.EV_KEY:

                    if event.value == KEY_PRESS:
                        for sink in pulse.sink_list():
                            if sink.mute:
                                log.debug('Received %s, unmuting sink %s', event, sink.description)
                                pulse.mute(sink, False)
                            else:
                                log.debug('Received %s, muting sink %s', event, sink.description)
                                pulse.mute(sink, True)

                # event action: volume
                elif event.type == ecodes.EV_REL:

                    if event.value == INCREASE:
                        log.debug('Received %s: increasing volume', event)
                        for sink in pulse.sink_list():
                            if sink.volume.value_flat == 1.0:
                                log.debug('Skipping volume increasing for sink %s', sink)
                            else:
                                log.debug('Adjusting sink %s', sink)
                                pulse.volume_change_all_chans(sink, INCREASE_AMOUNT)
                    else:
                        log.debug('Received %s: decreasing volume', event)
                        for sink in pulse.sink_list():
                            log.debug('Adjusting sink %s', sink)
                            pulse.volume_change_all_chans(sink, DECREASE_AMOUNT)

                else:

                    log.debug('Ignoring unknown event type %s', event.type)

    except IOError as e:

        if e.errno == errno.ENODEV:
            log.debug('Device unplugged')
        else:
            log.error(e.message)
            raise e

    except KeyboardInterrupt:
        log.debug('Terminating')


def run(device):
    if device is not None:
        listen_on(device)
    else:
        device = find_device()
        if len(device) == 0:
            log.error("Couldn't find device, try: powermated <device>")
            sys.exit(1)
        elif len(device) > 1:
            log.error("Multiple devices found, try: powermated <device>")
            sys.exit(1)
        else:
            listen_on(device[0])


def main():
    run(sys.argv[1] if len(sys.argv) > 1 else None)


if __name__ == "__main__":
    main()
