"""Planning discovery views: mock duration."""

import math


def _mock_duration(prop, destination):
    if prop.latitude is None or prop.longitude is None:
        return None
    latitude, longitude = (
        destination["location"]["latitude"],
        destination["location"]["longitude"],
    )
    lat1, lat2 = math.radians(float(prop.latitude)), math.radians(latitude)
    angle = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(math.radians(longitude - float(prop.longitude)) / 2) ** 2
    )
    kilometers = 6371 * 2 * math.asin(math.sqrt(min(1, max(0, angle))))
    speed = {"walking": 5, "cycling": 15, "driving": 30, "transit": 20}[
        destination["mode"]
    ]
    return math.ceil(kilometers / speed * 3600)
