import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/screens/rent_management_screen.dart';

class LeaseRentEntry extends StatelessWidget {
  const LeaseRentEntry({
    super.key,
    required this.leaseId,
    required this.propertyTitle,
    required this.workspace,
  });
  final String leaseId;
  final String propertyTitle;
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    icon: const Icon(Icons.receipt_long_outlined),
    label: AppText(LocaleKeys.journeyLeaseInvoices),
    onPressed: leaseId.isEmpty
        ? null
        : () => Go.to(
            RentManagementScreen(
              workspace: workspace,
              leaseId: leaseId,
              propertyTitle: propertyTitle,
            ),
          ),
  );
}
