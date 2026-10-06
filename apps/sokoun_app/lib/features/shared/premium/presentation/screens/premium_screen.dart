import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../widgets/premium_dashboard/premium_dashboard.dart';

class PremiumScreen extends StatelessWidget {
  const PremiumScreen({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.toolsTitle,
    showBackButton: true,
    body: PremiumDashboard(workspace: workspace),
  );
}
