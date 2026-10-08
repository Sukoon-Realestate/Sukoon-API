import 'package:sokoun_app/features/shared/premium/data/feature_service_capabilities.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_hosted_data.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_feedback.dart';
import '../../data/models/advanced_analytics_content.dart';
import 'advanced_analytics_empty_state.dart';

class AdvancedAnalyticsSummary extends StatelessWidget {
  const AdvancedAnalyticsSummary({super.key, required this.content});
  final AdvancedAnalyticsContent content;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      if (content.measuredAt != null)
        AppText(
          LocaleKeys.paidMeasuredAt.replaceAll(
            '{date}',
            DateFormat.yMMMd(
              Languages.currentLanguage.languageCode,
            ).add_Hm().format(content.measuredAt!.toLocal()),
          ),
        ),
      if (content.methodology.isNotEmpty) AppText(content.methodology),
      16.szH,
      if (content.metrics.isEmpty) const AdvancedAnalyticsEmptyState(),
      for (final metric in content.metrics)
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppText(metric.label, fontWeight: FontWeight.bold),
                8.szH,
                AppText(
                  metric.display,
                  fontWeight: FontWeight.bold,
                  fontSize: 24,
                ),
                if (metric.definition.isNotEmpty) AppText(metric.definition),
              ],
            ),
          ),
        ),
      if (FeatureServiceCapabilities.configured.analyticsExports &&
          PremiumHostedData.httpsUri(content.exportUrl) != null)
        OutlinedButton.icon(
          onPressed: () async {
            if (!await PremiumHostedData.open(content.exportUrl)) {
              PremiumFeedback.linkFailed();
            }
          },
          icon: const Icon(Icons.download_outlined),
          label: AppText(LocaleKeys.paidAnalyticsExport),
        ),
    ],
  );
}
