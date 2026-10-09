import 'models/owner_availability_content.dart';
import 'enums/owner_visit_request_state.dart';
import 'models/owner_visit_calendar_content.dart';
import '../../../shared/recovery/data/models/text_form_draft.dart';

abstract final class OwnerAvailabilityDraftData {
  static TextFormDraft capture(
    Map<String, List<OwnerAvailabilitySlotContent>> changes,
    DateTime selectedDate,
  ) => TextFormDraft({
    'selected_date': OwnerVisitCalendarContent.formatDate(selectedDate),
    for (final entry in changes.entries)
      for (final slot in entry.value)
        '${entry.key}|${slot.time}': '${slot.isEnabled}',
  });
  static Map<String, List<OwnerAvailabilitySlotContent>> restore(
    TextFormDraft draft,
  ) {
    final Map<String, List<OwnerAvailabilitySlotContent>> result = {};
    for (final entry in draft.fields.entries) {
      final parts = entry.key.split('|');
      if (parts.length != 2 ||
          DateTime.tryParse(parts.first) == null ||
          !RegExp(r'^\d{2}:\d{2}(:\d{2})?$').hasMatch(parts.last)) {
        continue;
      }
      (result[parts.first] ??= []).add(
        OwnerAvailabilitySlotContent(
          id: '',
          time: parts.last,
          isEnabled: entry.value == 'true',
          state: entry.value == 'true' ? 'available' : 'unspecified',
          visit: null,
        ),
      );
    }
    return result;
  }

  static ({List<OwnerAvailabilitySlotContent> slots, bool conflict}) reconcile(
    List<OwnerAvailabilitySlotContent> draft,
    List<OwnerAvailabilitySlotContent> fresh,
  ) {
    final Map<String, OwnerAvailabilitySlotContent> result = {
      for (final slot in draft) slot.time: slot,
    };
    bool conflict = false;
    for (final slot in fresh) {
      if (!slot.slotState.isBooked) continue;
      if (result[slot.time]?.isEnabled != slot.isEnabled) conflict = true;
      result[slot.time] = slot;
    }
    return (
      slots: result.values.toList()..sort((a, b) => a.time.compareTo(b.time)),
      conflict: conflict,
    );
  }
}
