from evdev import InputDevice, ecodes, list_devices
import subprocess
import sys
import errno
import logging

VOLUME_CMD = ['amixer', '-D', 'pulse', 'sset', 'Master']
MUTE_TOGGLE = 0

log = logging.getLogger('powermated')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))


def find_device():
    log.info("Searching for Griffin Powermate input device")
    devices = [InputDevice(fn) for fn in list_devices()]
    for device in devices:
        if device.name.find('PowerMate') != -1:
            log.info(f"Device found: ${device.name} (${device.phys})")
            return [device.fn]
    return []


def run_process(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stdout:
        log.debug(stdout)
    if stderr:
        log.debug(stderr)


def listen_on(device):
    """
    Monitor the given device and modify the sound volume

    :param device: the name of the device to read
    """

    log.debug('Listening on ' + device)

    try:

        for event in InputDevice(device).read_loop():

            # ignore synchronization events
            if event.type == ecodes.EV_SYN:
                continue

            log.debug(f'Received event: ${event}')

            # event action: mute
            if event.type == ecodes.EV_KEY:

                cmd = VOLUME_CMD[:]
                cmd.append('toggle')

                if event.value == MUTE_TOGGLE:
                    run_process(cmd)

            # event action: volume
            elif event.type == ecodes.EV_REL:

                cmd = VOLUME_CMD[:]
                cmd.append(str(abs(event.value)) + '%')

                if event.value > 0:
                    cmd[-1] += '+'
                else:
                    cmd[-1] += '-'

                run_process(cmd)

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
