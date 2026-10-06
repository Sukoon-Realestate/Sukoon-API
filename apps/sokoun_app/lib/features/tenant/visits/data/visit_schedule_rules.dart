import 'package:timezone/data/latest.dart' as time_zone_data;
import 'package:timezone/timezone.dart' as time_zone;

/// Property appointments are expressed in the property's Egyptian time zone.
/// Device time zones and daylight saving changes must not move the appointment.
abstract final class VisitScheduleRules {
  static bool _initialized = false;

  static DateTime now({DateTime? instant}) {
    if (!_initialized) {
      time_zone_data.initializeTimeZones();
      _initialized = true;
    }
    return time_zone.TZDateTime.from(
      instant ?? DateTime.now(),
      time_zone.getLocation('Africa/Cairo'),
    );
  }

  static DateTime? date(String value) {
    if (!RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(value)) return null;
    final parsed = DateTime.tryParse(value);
    if (parsed == null || parsed.toIso8601String().substring(0, 10) != value) {
      return null;
    }
    return parsed;
  }

  static ({int hour, int minute, int second})? time(String value) {
    final match = RegExp(r'^(\d{2}):(\d{2})(?::(\d{2}))?$').firstMatch(value);
    if (match == null) return null;
    final hour = int.parse(match[1]!);
    final minute = int.parse(match[2]!);
    final second = int.parse(match[3] ?? '0');
    return hour < 24 && minute < 60 && second < 60
        ? (hour: hour, minute: minute, second: second)
        : null;
  }

  static DateTime? appointment(String visitDate, String visitTime) {
    final day = date(visitDate);
    final slot = time(visitTime);
    if (day == null || slot == null) return null;
    now();
    final appointment = time_zone.TZDateTime(
      time_zone.getLocation('Africa/Cairo'),
      day.year,
      day.month,
      day.day,
      slot.hour,
      slot.minute,
      slot.second,
    );
    // Reject a nonexistent local time during the daylight saving transition.
    if (appointment.year != day.year ||
        appointment.month != day.month ||
        appointment.day != day.day ||
        appointment.hour != slot.hour ||
        appointment.minute != slot.minute) {
      return null;
    }
    return appointment;
  }

  static bool isFuture(
    String visitDate,
    String visitTime, {
    DateTime? instant,
  }) =>
      appointment(visitDate, visitTime)?.isAfter(now(instant: instant)) ??
      false;

  static bool isTodayOrLater(String value, {DateTime? instant}) {
    final day = date(value);
    final current = now(instant: instant);
    return day != null &&
        !day.isBefore(DateTime(current.year, current.month, current.day));
  }
}
