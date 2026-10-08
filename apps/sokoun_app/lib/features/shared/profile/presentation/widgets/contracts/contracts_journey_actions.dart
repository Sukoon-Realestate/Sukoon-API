import 'package:flutter/material.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/digital_leases_entry.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitations_entry.dart';

class ContractsJourneyActions extends StatelessWidget {
  const ContractsJourneyActions({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => Card(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        DigitalLeasesEntry(workspace: workspace),
        const Divider(height: 1),
        TenancyInvitationsEntry(workspace: workspace),
      ],
    ),
  );
}
