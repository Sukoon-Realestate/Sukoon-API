import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../widgets/premium_alert_detail_content.dart';

class PremiumAlertDetailScreen extends StatelessWidget {
  const PremiumAlertDetailScreen({super.key, required this.alertId});
  final String alertId;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.paidPriorityAlerts,
    showBackButton: true,
    body: PremiumAlertDetailContent(alertId: alertId),
  );
}
