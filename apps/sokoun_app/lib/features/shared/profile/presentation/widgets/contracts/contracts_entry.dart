import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import '../../../imports.dart';

class ContractsEntry extends StatelessWidget {
  const ContractsEntry({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => ListTile(
    leading: const Icon(Icons.description_outlined),
    title: AppText(LocaleKeys.profileContracts),
    subtitle: AppText(LocaleKeys.journeyContractsEntryBody),
    trailing: const Icon(Icons.chevron_right),
    onTap: () => WorkspaceNavigation.open(
      workspace: workspace,
      detail: () => Go.to(ProfileContractsScreen(workspace: workspace)),
    ),
  );
}
