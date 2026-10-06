import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import '../../screens/premium_property_picker_screen.dart';

class PremiumPropertySelector extends StatelessWidget {
  const PremiumPropertySelector({
    super.key,
    required this.property,
    required this.onSelected,
    this.enabled = true,
  });
  final OwnerPropertyContent? property;
  final ValueChanged<OwnerPropertyContent> onSelected;
  final bool enabled;
  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    onPressed: !enabled
        ? null
        : () async {
            final selected = await Go.to<OwnerPropertyContent>(
              const PremiumPropertyPickerScreen(),
            );
            if (selected != null && context.mounted) onSelected(selected);
          },
    icon: const Icon(Icons.home_outlined),
    label: AppText(property?.title ?? LocaleKeys.paidSelectProperty),
  );
}
