import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../screens/digital_leases_screen.dart';

/// Already inside the authenticated Contracts workspace.
class DigitalLeasesEntry extends StatelessWidget {
  const DigitalLeasesEntry({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => ListTile(
    leading: const Icon(Icons.draw_outlined),
    title: AppText(LocaleKeys.paidDigitalLeases),
    subtitle: AppText(LocaleKeys.journeyDigitalLeasesBody),
    trailing: const Icon(Icons.chevron_right),
    onTap: () => Go.to(DigitalLeasesScreen(workspace: workspace)),
  );
}
