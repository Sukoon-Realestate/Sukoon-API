import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intl/intl.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';
import 'package:sokoun_app/features/shared/premium/data/feature_service_capabilities.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_detail_field.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../../data/models/premium_search_alert.dart';
import 'alert_filters_summary.dart';

class PremiumAlertDetailsView extends StatelessWidget {
  const PremiumAlertDetailsView({
    super.key,
    required this.alert,
    required this.options,
  });
  final PremiumSearchAlert alert;
  final PropertyFilterOptionsModel options;
  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    child: SokounContent(
      child: Padding(
        padding: EdgeInsets.all(20.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 16.h,
          children: [
            AppText(alert.name, fontWeight: FontWeight.bold, fontSize: 20.sp),
            PremiumStatusBadge(
              status: alert.enabled
                  ? PremiumStatus.active
                  : PremiumStatus.paused,
            ),
            FeatureDetailField(
              label: LocaleKeys.paidAlertCadence,
              value: switch (alert.cadence) {
                'instant' => LocaleKeys.paidAlertInstant,
                'daily' => LocaleKeys.paidAlertDaily,
                _ => alert.cadence,
              },
            ),
            if (alert.lastMatchedAt != null)
              FeatureDetailField(
                label: LocaleKeys.featureAlertLastMatch,
                value: DateFormat.yMMMd(
                  Languages.currentLanguage.languageCode,
                ).add_Hm().format(alert.lastMatchedAt!.toLocal()),
              ),
            AlertFiltersSummary(filters: alert.filters, options: options),
            if (!FeatureServiceCapabilities.configured.alertDelivery)
              AppText(LocaleKeys.featureAlertDeliveryUnavailable),
            FilledButton.icon(
              onPressed: () => Go.to(
                TenantSearchResultsScreen(initialFilters: alert.filters),
              ),
              icon: const Icon(Icons.search),
              label: AppText(LocaleKeys.paidAlertOpenResults),
            ),
          ],
        ),
      ),
    ),
  );
}
