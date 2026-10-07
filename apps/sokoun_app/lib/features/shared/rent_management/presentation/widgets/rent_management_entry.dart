import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import '../screens/rent_management_screen.dart';

class RentManagementEntry extends StatelessWidget {
  const RentManagementEntry({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => ListTile(
    leading: const Icon(Icons.receipt_long_outlined),
    title: AppText(LocaleKeys.paidRentManagement),
    subtitle: AppText(LocaleKeys.journeyRentEntryBody),
    trailing: const Icon(Icons.chevron_right),
    onTap: () => WorkspaceNavigation.open(
      workspace: workspace,
      detail: () => Go.to(RentManagementScreen(workspace: workspace)),
    ),
  );
}
