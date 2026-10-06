import 'package:geocoding/geocoding.dart' as geocoding;
import 'package:geolocator/geolocator.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;

import 'models/current_location_area.dart';

abstract interface class CurrentLocationDataSource {
  Future<bool> isServiceEnabled();
  Future<bool> openLocationSettings();
  Future<CurrentLocationArea> resolveArea({required String languageCode});
}

class NativeCurrentLocationDataSource implements CurrentLocationDataSource {
  const NativeCurrentLocationDataSource();

  @override
  Future<bool> isServiceEnabled() => Geolocator.isLocationServiceEnabled();

  @override
  Future<bool> openLocationSettings() => Geolocator.openLocationSettings();

  @override
  Future<CurrentLocationArea> resolveArea({
    required String languageCode,
  }) async {
    final position = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.medium,
        timeLimit: Duration(seconds: 15),
      ),
    );
    await geocoding.setLocaleIdentifier(languageCode);
    final places = await geocoding
        .placemarkFromCoordinates(position.latitude, position.longitude)
        .timeout(const Duration(seconds: 10));
    for (final place in places) {
      final city = _firstNonEmpty([
        place.locality,
        place.subAdministrativeArea,
        place.administrativeArea,
      ]);
      final area = CurrentLocationArea(
        city: city,
        district: place.subLocality ?? '',
      );
      if (area.searchQuery.isNotEmpty) return area;
    }
    throw StateError('No searchable area was returned for this location.');
  }

  String _firstNonEmpty(List<String?> values) => values
      .map((value) => value?.trim() ?? '')
      .firstWhere((value) => value.isNotEmpty, orElse: () => '');
}

abstract final class CurrentLocationData {
  static CurrentLocationDataSource get source =>
      injector.isRegistered<CurrentLocationDataSource>()
      ? injector<CurrentLocationDataSource>()
      : const NativeCurrentLocationDataSource();
}
