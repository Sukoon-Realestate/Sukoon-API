import 'package:flutter/material.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/digital_leases_entry.dart';

class ContractsJourneyActions extends StatelessWidget {
  const ContractsJourneyActions({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) =>
      Card(child: DigitalLeasesEntry(workspace: workspace));
}
