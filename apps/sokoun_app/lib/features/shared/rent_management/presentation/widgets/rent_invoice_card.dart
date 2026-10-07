import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
import '../../data/models/rent_invoice.dart';
import '../screens/rent_invoice_screen.dart';

class RentInvoiceCard extends StatelessWidget {
  const RentInvoiceCard({
    super.key,
    required this.invoice,
    required this.workspace,
    required this.onReturned,
  });
  final RentInvoice invoice;
  final AppWorkspace workspace;
  final VoidCallback onReturned;
  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      title: AppText(invoice.propertyTitle, fontWeight: FontWeight.bold),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(invoice.reference),
          AppText(invoice.amount.display),
          PremiumStatusBadge(status: invoice.status),
          if (invoice.dueDate != null)
            AppText(
              '${LocaleKeys.paidDueDate} ${DateFormat.yMMMd(Languages.currentLanguage.languageCode).format(invoice.dueDate!)}',
            ),
        ],
      ),
      onTap: invoice.id.isEmpty
          ? null
          : () async {
              await Go.to(
                RentInvoiceScreen(invoiceId: invoice.id, workspace: workspace),
              );
              if (context.mounted) onReturned();
            },
    ),
  );
}
