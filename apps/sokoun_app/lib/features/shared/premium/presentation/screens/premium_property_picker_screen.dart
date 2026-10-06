import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../widgets/shared/premium_property_picker_list.dart';

class PremiumPropertyPickerScreen extends StatelessWidget {
  const PremiumPropertyPickerScreen({super.key});
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.paidSelectProperty,
    showBackButton: true,
    body: const PremiumPropertyPickerList(),
  );
}
