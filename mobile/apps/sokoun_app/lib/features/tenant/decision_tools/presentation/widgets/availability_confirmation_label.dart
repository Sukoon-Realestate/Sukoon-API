import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/visits/data/visit_schedule_rules.dart';

class AvailabilityConfirmationLabel extends StatelessWidget {
  const AvailabilityConfirmationLabel({super.key, required this.confirmedAt});
  final DateTime? confirmedAt;
  @override
  Widget build(BuildContext context) {
    final timestamp = confirmedAt;
    final known = timestamp != null && !timestamp.isAfter(DateTime.now());
    final message = known
        ? LocaleKeys.freeAvailabilityConfirmed.replaceAll(
            '{date}',
            MaterialLocalizations.of(
              context,
            ).formatMediumDate(VisitScheduleRules.now(instant: timestamp)),
          )
        : LocaleKeys.freeAvailabilityUnknown;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Icon(Icons.update, size: 20),
        const SizedBox(width: 8),
        Expanded(child: AppText(message, height: 1.5)),
      ],
    );
  }
}
