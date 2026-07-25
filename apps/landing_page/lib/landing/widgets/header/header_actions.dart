import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import '../shared/landing_button.dart';

class HeaderActions extends StatelessWidget {
  const HeaderActions({
    required this.showMenuSpacing,
    required this.onNavigate,
    super.key,
  });

  final bool showMenuSpacing;
  final ValueChanged<String> onNavigate;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        LandingButton(
          label: LocaleKeys.landingLogin,
          onPressed: () => onNavigate('hero'),
          backgroundColor: Colors.transparent,
          foregroundColor: LandingColors.navy,
          borderColor: LandingColors.border,
          height: 40,
          horizontalPadding: 18,
          radius: 10,
        ),
        const SizedBox(width: 10),
        LandingButton(
          label: LocaleKeys.landingStartNow,
          onPressed: () => onNavigate('hero'),
          height: 40,
          horizontalPadding: 18,
          radius: 10,
        ),
        if (showMenuSpacing) const SizedBox(width: 8),
      ],
    );
  }
}
