import uuid
import resources.lib.modules.control as control

try:
    import dummy
    IS_TEST = not control.isKodi
except:
    IS_TEST = False


def get_user():
    return control.setting('oiplay_account') if not IS_TEST else dummy.user


def get_password():
    return control.setting('oiplay_password') if not IS_TEST else dummy.password


def get_device_id():
    device_id = control.setting('oiplay_device_id')
    if not device_id:
        device_id = str(uuid.uuid4()).upper()
        control.setSetting('oiplay_device_id', device_id)

    return device_id
