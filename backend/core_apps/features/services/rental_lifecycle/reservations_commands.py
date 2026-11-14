"""Named reservations commands; adapters supply typed data and current actor."""

from core_apps.features.services.rental_lifecycle import reservations as service


def reservation_holds_post_execute(prop, *, actor, data, external):
    item = service.create_hold(prop, actor, data, external=external)
    return (item, service.hold_payload(item, actor), 201)


def reservation_hold_post_execute(item, *, action, actor, data):
    item = service.change_hold(item, actor, data, action)
    return (item, service.hold_payload(item, actor), 200)
