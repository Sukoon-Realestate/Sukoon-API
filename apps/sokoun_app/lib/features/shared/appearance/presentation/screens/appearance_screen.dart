import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';

import '../widgets/appearance_content.dart';

class AppearanceScreen extends StatelessWidget {
  const AppearanceScreen({super.key});

  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.appearanceTitle,
    contentWidth: SokounContentWidth.form,
    body: const SafeArea(child: AppearanceContent()),
  );
}
