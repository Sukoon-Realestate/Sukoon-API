import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';
import '../../data/models/premium_search_alert.dart';
import '../cubits/premium_alert_details_cubit.dart';
import 'premium_alerts_empty_state.dart';

class PremiumAlertDetailContent extends StatefulWidget {
  const PremiumAlertDetailContent({super.key, required this.alertId});
  final String alertId;
  @override
  State<PremiumAlertDetailContent> createState() =>
      _PremiumAlertDetailContentState();
}

class _PremiumAlertDetailContentState extends State<PremiumAlertDetailContent> {
  late final PremiumAlertDetailsCubit _cubit;
  late final Future<void> _request;
  @override
  void initState() {
    super.initState();
    _cubit = PremiumAlertDetailsCubit();
    _request = _cubit.load(widget.alertId);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      PremiumRemoteView<PremiumAlertDetailsCubit, PremiumSearchAlert>(
        cubit: _cubit,
        request: _request,
        initialData: const PremiumSearchAlert.initial(),
        onRetry: () => _cubit.load(widget.alertId),
        builder: (alert) => alert.id.isEmpty
            ? const PremiumAlertsEmptyState()
            : SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    AppText(alert.name, fontWeight: FontWeight.bold),
                    AppText(alert.filters.combinedSearch),
                    FilledButton.icon(
                      onPressed: () => Go.to(
                        TenantSearchResultsScreen(
                          initialFilters: alert.filters,
                        ),
                      ),
                      icon: const Icon(Icons.search),
                      label: AppText(LocaleKeys.paidAlertOpenResults),
                    ),
                  ],
                ),
              ),
      );
}
