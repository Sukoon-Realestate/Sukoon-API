import 'dart:convert';
import 'dart:io';
import 'dart:ui' show Rect;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'enums/visit_status.dart';
import 'models/tenant_visit_content.dart';
import 'visit_schedule_rules.dart';

abstract final class VisitCalendarData {
  static String _escape(String value) => value
      .replaceAll('\\', '\\\\')
      .replaceAll('\r', '')
      .replaceAll('\n', '\\n')
      .replaceAll(';', '\\;')
      .replaceAll(',', '\\,');
  static String _utc(DateTime value) =>
      '${value.toUtc().toIso8601String().substring(0, 19).replaceAll('-', '').replaceAll(':', '')}Z';
  static String _fold(String line) {
    final buffer = StringBuffer();
    var bytes = 0;
    for (final rune in line.runes) {
      final character = String.fromCharCode(rune);
      final count = utf8.encode(character).length;
      if (bytes + count > 75) {
        buffer.write('\r\n ');
        bytes = 1;
      }
      buffer.write(character);
      bytes += count;
    }
    return buffer.toString();
  }

  static String? build(TenantVisitContent visit, {DateTime? generatedAt}) {
    final start = VisitScheduleRules.appointment(
      visit.visitDate,
      visit.visitTime,
    );
    if (!visit.status.isAccepted || visit.id.isEmpty || start == null) {
      return null;
    }
    final lines = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Sokoun//Viewings//EN',
      'CALSCALE:GREGORIAN',
      'BEGIN:VEVENT',
      'UID:sokoun-visit-${Uri.encodeComponent(visit.id)}@sokoun.app',
      'DTSTAMP:${_utc(generatedAt ?? DateTime.now())}',
      'DTSTART:${_utc(start)}',
      'SUMMARY:${_escape(visit.propertyTitle)}',
      'STATUS:CONFIRMED',
      'BEGIN:VALARM',
      'TRIGGER:-PT1H',
      'ACTION:DISPLAY',
      'DESCRIPTION:${_escape(visit.propertyTitle)}',
      'END:VALARM',
      'END:VEVENT',
      'END:VCALENDAR',
    ];
    return '${lines.map(_fold).join('\r\n')}\r\n';
  }

  static Future<void> share(
    TenantVisitContent visit, {
    required Rect origin,
  }) async {
    final calendar = build(visit);
    if (calendar == null) {
      throw StateError(
        'A confirmed appointment with an exact date and time is required.',
      );
    }
    final directory = await getTemporaryDirectory();
    final file = File(
      '${directory.path}/sokoun_visit_${Uri.encodeComponent(visit.id)}.ics',
    );
    await file.writeAsString(calendar, flush: true);
    await SharePlus.instance.share(
      ShareParams(
        files: [XFile(file.path, mimeType: 'text/calendar')],
        subject: visit.propertyTitle,
        sharePositionOrigin: origin,
      ),
    );
  }
}
