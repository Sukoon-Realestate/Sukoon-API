import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import '../../screens/premium_screen.dart';

class PremiumEntryTile extends StatelessWidget {
  const PremiumEntryTile({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      leading: Icon(
        Icons.apps_outlined,
        color: context.appColor(AppColors.sokoonTeal),
      ),
      title: AppText(LocaleKeys.toolsTitle, fontWeight: FontWeight.bold),
      subtitle: AppText(LocaleKeys.toolsSubtitle),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => WorkspaceNavigation.open(
        workspace: workspace,
        detail: () => Go.to(PremiumScreen(workspace: workspace)),
      ),
    ),
  );
}
