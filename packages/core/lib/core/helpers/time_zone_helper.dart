import 'package:timezone/data/latest.dart' as database;
import 'package:timezone/timezone.dart' as timezone;

abstract final class TimeZoneHelper {
  static bool _initialized = false;

  /// Converts an instant using the location's daylight-saving rules.
  static DateTime inLocation(String location, {DateTime? instant}) {
    if (!_initialized) {
      database.initializeTimeZones();
      _initialized = true;
    }
    return timezone.TZDateTime.from(
      instant ?? DateTime.now(),
      timezone.getLocation(location),
    );
  }
}
