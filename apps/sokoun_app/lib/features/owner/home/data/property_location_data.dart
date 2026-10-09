import 'dart:developer';

import 'package:geocoding/geocoding.dart' as geocoding;
import 'package:geolocator/geolocator.dart';

import 'models/property_location.dart';

enum PropertyLocationFailure {
  serviceDisabled,
  permissionDenied,
  permissionDeniedForever,
  unavailable,
  noResults,
}

abstract interface class PropertyLocationDataSource {
  Future<List<PropertyLocation>> search(String query);
  Future<PropertyLocation> currentLocation();
  Future<String> addressFor(PropertyLocation location);
  Future<bool> openSettings({required bool appSettings});
}

class NativePropertyLocationData implements PropertyLocationDataSource {
  const NativePropertyLocationData();

  @override
  Future<List<PropertyLocation>> search(String query) async {
    final locations = await geocoding
        .locationFromAddress(query)
        .timeout(const Duration(seconds: 12));
    for (geocoding.Location location in locations) {
      log('the valid location is ${location.latitude}');
    }
    return locations
        .map(
          (location) => PropertyLocation(
            latitude: location.latitude,
            longitude: location.longitude,
          ),
        )
        .where((location) => location.isValid)
        .take(5)
        .toList(growable: false);
  }

  @override
  Future<PropertyLocation> currentLocation() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw PropertyLocationFailure.serviceDisabled;
    }
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.deniedForever) {
      throw PropertyLocationFailure.permissionDeniedForever;
    }
    if (permission != LocationPermission.whileInUse &&
        permission != LocationPermission.always) {
      throw PropertyLocationFailure.permissionDenied;
    }
    final position = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        timeLimit: Duration(seconds: 15),
      ),
    );
    return PropertyLocation(
      latitude: position.latitude,
      longitude: position.longitude,
    );
  }

  @override
  Future<String> addressFor(PropertyLocation location) async {
    final places = await geocoding
        .placemarkFromCoordinates(location.latitude, location.longitude)
        .timeout(const Duration(seconds: 8));
    if (places.isEmpty) return '';
    final place = places.first;
    return [
          place.street,
          place.subLocality,
          place.locality,
          place.administrativeArea,
        ]
        .whereType<String>()
        .map((part) => part.trim())
        .where((part) => part.isNotEmpty)
        .toSet()
        .join(', ');
  }

  @override
  Future<bool> openSettings({required bool appSettings}) => appSettings
      ? Geolocator.openAppSettings()
      : Geolocator.openLocationSettings();
}
