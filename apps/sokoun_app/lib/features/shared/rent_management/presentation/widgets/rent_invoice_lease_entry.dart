import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/digital_lease_details_screen.dart';

class RentInvoiceLeaseEntry extends StatelessWidget {
  const RentInvoiceLeaseEntry({
    super.key,
    required this.leaseId,
    required this.workspace,
  });
  final String leaseId;
  final AppWorkspace workspace;

  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    icon: const Icon(Icons.description_outlined),
    label: AppText(LocaleKeys.journeyViewLease),
    onPressed: () => Go.to(
      DigitalLeaseDetailsScreen(leaseId: leaseId, workspace: workspace),
    ),
  );
}
