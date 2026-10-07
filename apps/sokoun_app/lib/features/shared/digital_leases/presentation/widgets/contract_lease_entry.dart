import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../screens/digital_lease_details_screen.dart';

class ContractLeaseEntry extends StatelessWidget {
  const ContractLeaseEntry({
    super.key,
    required this.leaseId,
    required this.workspace,
  });
  final String leaseId;
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    icon: const Icon(Icons.draw_outlined),
    label: AppText(LocaleKeys.journeyViewLease),
    onPressed: leaseId.isEmpty
        ? null
        : () => Go.to(
            DigitalLeaseDetailsScreen(leaseId: leaseId, workspace: workspace),
          ),
  );
}
