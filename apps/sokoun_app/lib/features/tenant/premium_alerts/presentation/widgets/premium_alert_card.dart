import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
import '../../data/models/premium_search_alert.dart';
import '../screens/premium_alert_detail_screen.dart';

class PremiumAlertCard extends StatelessWidget {
  const PremiumAlertCard({
    super.key,
    required this.alert,
    required this.onToggle,
    required this.onRemove,
    required this.canChange,
  });
  final PremiumSearchAlert alert;
  final VoidCallback onToggle;
  final VoidCallback onRemove;
  final bool canChange;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(alert.name, fontWeight: FontWeight.bold),
          if (alert.filters.combinedSearch.isNotEmpty)
            AppText(alert.filters.combinedSearch),
          PremiumStatusBadge(
            status: alert.enabled ? PremiumStatus.active : PremiumStatus.paused,
          ),
          Wrap(
            spacing: 8,
            children: [
              TextButton(
                onPressed: () =>
                    Go.to(PremiumAlertDetailScreen(alertId: alert.id)),
                child: AppText(LocaleKeys.featureAlertDetails),
              ),
              TextButton(
                onPressed: () => Go.to(
                  TenantSearchResultsScreen(initialFilters: alert.filters),
                ),
                child: AppText(LocaleKeys.paidAlertOpenResults),
              ),
              if (alert.canManage && alert.revision > 0)
                TextButton(
                  onPressed: canChange ? onToggle : null,
                  child: AppText(
                    alert.enabled
                        ? LocaleKeys.paidAlertPause
                        : LocaleKeys.paidAlertResume,
                  ),
                ),
              if (alert.canManage && alert.revision > 0)
                TextButton.icon(
                  onPressed: canChange ? onRemove : null,
                  icon: const Icon(Icons.delete_outline),
                  label: AppText(LocaleKeys.freeRemove),
                ),
            ],
          ),
        ],
      ),
    ),
  );
}
