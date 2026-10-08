import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intl/intl.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_detail_field.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_selection_panel.dart';
import '../../data/models/rent_invoice.dart';

class RentInvoiceSummary extends StatelessWidget {
  const RentInvoiceSummary({super.key, required this.invoice});
  final RentInvoice invoice;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 16.h,
    children: [
      AppText(
        invoice.propertyTitle,
        fontWeight: FontWeight.bold,
        fontSize: 20.sp,
      ),
      PremiumStatusBadge(status: invoice.status),
      Card(
        child: Padding(
          padding: EdgeInsets.all(16.w),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 12.h,
            children: [
              FeatureDetailField(
                label: LocaleKeys.paidRentReference,
                value: invoice.reference,
              ),
              AppText(
                LocaleKeys.featureInvoiceAmount,
                fontWeight: FontWeight.w600,
              ),
              AppText(
                invoice.amount.display,
                fontWeight: FontWeight.bold,
                fontSize: 24.sp,
              ),
              AppText(LocaleKeys.featureStoredAccountingAmount),
              if (invoice.dueDate != null)
                FeatureDetailField(
                  label: LocaleKeys.paidDueDate,
                  value: DateFormat.yMMMd(
                    Languages.currentLanguage.languageCode,
                  ).format(invoice.dueDate!),
                ),
            ],
          ),
        ),
      ),
      if (invoice.rentalSelection != null)
        RentalSelectionPanel(
          selection: invoice.rentalSelection!,
          historical: true,
        ),
    ],
  );
}
