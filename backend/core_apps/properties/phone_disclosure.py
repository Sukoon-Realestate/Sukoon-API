"""Registration contact data is never disclosed to another application user.

Empty compatibility fields keep older clients safe during the mobile rollout.
No visit or rental state grants phone disclosure.
"""


def is_phone_disclosed(viewer, counterpart, property_obj=None, visit=None):
    return False


def counterpart_phone_payload(*, viewer, counterpart, request=None, property_obj=None, visit=None):
    return {"phone_number": "", "masked_phone_number": "", "is_phone_revealed": False, "phone_notice": ""}
