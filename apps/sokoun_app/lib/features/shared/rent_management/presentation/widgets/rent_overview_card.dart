import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
import '../../data/models/rent_invoice.dart';
import '../screens/rent_invoice_screen.dart';

class RentOverviewCard extends StatelessWidget {
  const RentOverviewCard({
    super.key,
    required this.invoice,
    required this.isCached,
    required this.onReturned,
  });
  final RentInvoice invoice;
  final bool isCached;
  final Future<void> Function() onReturned;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(LocaleKeys.journeyRentDue, fontWeight: FontWeight.bold),
          8.szH,
          AppText(invoice.propertyTitle),
          if (invoice.rentalSelection != null)
            AppText(RentalOfferLabels.accommodation(invoice.rentalSelection!)),
          AppText(
            invoice.amount.display,
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: context.appColor(AppColors.sokoonTeal),
          ),
          PremiumStatusBadge(status: invoice.status),
          if (invoice.dueDate != null)
            AppText(
              '${LocaleKeys.paidDueDate} ${DateFormat.yMMMd(Languages.currentLanguage.languageCode).format(invoice.dueDate!)}',
            ),
          if (isCached) AppText(LocaleKeys.journeyRentCached),
          8.szH,
          FilledButton.icon(
            onPressed: invoice.id.isEmpty
                ? null
                : () async {
                    await Go.to(
                      RentInvoiceScreen(
                        invoiceId: invoice.id,
                        workspace: AppWorkspace.tenant,
                      ),
                    );
                    if (context.mounted) await onReturned();
                  },
            icon: const Icon(Icons.receipt_long_outlined),
            label: AppText(LocaleKeys.journeyViewInvoice),
          ),
        ],
      ),
    ),
  );
}
