import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intl/intl.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_detail_field.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_selection_panel.dart';
import '../../data/models/digital_lease.dart';

class LeaseDetailsSummary extends StatelessWidget {
  const LeaseDetailsSummary({super.key, required this.lease});
  final DigitalLease lease;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 16.h,
    children: [
      AppText(
        lease.propertyTitle,
        fontWeight: FontWeight.bold,
        fontSize: 20.sp,
      ),
      PremiumStatusBadge(status: lease.status),
      Card(
        child: Padding(
          padding: EdgeInsets.all(16.w),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 12.h,
            children: [
              FeatureDetailField(
                label: LocaleKeys.paidMonthlyRent,
                value: lease.rent.display,
              ),
              AppText(LocaleKeys.featureStoredAccountingAmount),
              if (lease.ownerName.isNotEmpty)
                FeatureDetailField(
                  label: LocaleKeys.featureLeaseOwner,
                  value: lease.ownerName,
                ),
              if (lease.tenantName.isNotEmpty)
                FeatureDetailField(
                  label: LocaleKeys.ownerVisitTenantLabel,
                  value: lease.tenantName,
                ),
              if (lease.startDate != null)
                FeatureDetailField(
                  label: LocaleKeys.paidLeaseStart,
                  value: DateFormat.yMMMd(
                    Languages.currentLanguage.languageCode,
                  ).format(lease.startDate!),
                ),
              if (lease.endDate != null)
                FeatureDetailField(
                  label: LocaleKeys.paidLeaseEnd,
                  value: DateFormat.yMMMd(
                    Languages.currentLanguage.languageCode,
                  ).format(lease.endDate!),
                ),
            ],
          ),
        ),
      ),
      if (lease.rentalSelection != null)
        RentalSelectionPanel(
          selection: lease.rentalSelection!,
          historical: true,
        ),
    ],
  );
}
