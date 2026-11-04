"""Optional owner classification; it never merges physical capture components."""
from .capture_validation import fields, identifier
from .errors import require

STATES = {"incomplete", "complete", "unavailable"}


def validate(plan, session, physical_stations, captured_rooms):
    fields(plan, {"schemaVersion", "revision", "rooms", "stations"})
    require(type(plan["schemaVersion"]) is int and plan["schemaVersion"] == 1 and type(plan["revision"]) is int and plan["revision"] >= 1,
        "MANIFEST_INVALID", "Choose a current coverage-plan revision.")
    require(isinstance(plan["rooms"], list) and 1 <= len(plan["rooms"]) <= 40
        and isinstance(plan["stations"], list) and len(plan["stations"]) <= 200,
        "MANIFEST_INVALID", "The capture plan exceeds its bounds.")
    known_rooms = {str(value) for value in session.rooms.values_list("client_id", flat=True)}
    rooms, station_ids, physical_ids = set(), set(), set()
    def common(row):
        require(identifier(row["id"]) and isinstance(row["label"], str) and 1 <= len(row["label"].strip()) <= 80
            and isinstance(row["ownerStatus"], str) and row["ownerStatus"] in STATES and type(row["revision"]) is int and row["revision"] >= 1,
            "MANIFEST_INVALID", "Capture names, revisions and owner review states must be explicit.")
    for room in plan["rooms"]:
        fields(room, {"id", "label", "ownerStatus", "revision"}); common(room)
        require(room["id"] in known_rooms and room["id"] not in rooms,
            "MANIFEST_INVALID", "A planned room must belong to this capture session.")
        require(room["ownerStatus"] != "complete" or room["id"] in captured_rooms,
            "MANIFEST_INVALID", "Capture evidence before marking a room reviewed.")
        rooms.add(room["id"])
    for station in plan["stations"]:
        fields(station, {"id", "roomId", "label", "ownerStatus", "revision", "nativeStationIds"}); common(station)
        attempts = station["nativeStationIds"]
        require(station["id"] not in station_ids and identifier(station["roomId"]) and station["roomId"] in rooms
            and isinstance(attempts, list) and len(attempts) <= 5000 and all(identifier(value) for value in attempts)
            and len(set(attempts)) == len(attempts),
            "MANIFEST_INVALID", "Stations need unique identities within their named rooms.")
        for identity in attempts:
            require(identity in physical_stations and physical_stations[identity][0] == station["roomId"]
                and identity not in physical_ids,
                "MANIFEST_INVALID", "A physical station cannot be relabeled into another room or logical station.")
            physical_ids.add(identity)
        require(station["ownerStatus"] != "complete" or bool(attempts),
            "MANIFEST_INVALID", "Capture evidence before marking a station reviewed.")
        station_ids.add(station["id"])
    return plan
