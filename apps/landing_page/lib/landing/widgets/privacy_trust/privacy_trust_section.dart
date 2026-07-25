import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import '../shared/imports.dart';
import 'privacy_trust_card.dart';

class PrivacyTrustSection extends StatelessWidget {
  const PrivacyTrustSection({super.key});

  static List<(IconData, String, String)> get _items => [
    (
      Icons.visibility_off_outlined,
      LocaleKeys.landingPrivacyHiddenNumberTitle,
      LocaleKeys.landingPrivacyHiddenNumberBody,
    ),
    (
      Icons.lock_outline_rounded,
      LocaleKeys.landingPrivacyIdentityTitle,
      LocaleKeys.landingPrivacyIdentityBody,
    ),
    (
      Icons.shield_outlined,
      LocaleKeys.landingPrivacyOwnershipTitle,
      LocaleKeys.landingPrivacyOwnershipBody,
    ),
    (
      Icons.chat_bubble_outline_rounded,
      LocaleKeys.landingPrivacyChatTitle,
      LocaleKeys.landingPrivacyChatBody,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return SectionSpacing(
      gradient: const LinearGradient(
        begin: Alignment.topRight,
        end: Alignment.bottomLeft,
        stops: [0, 0.6, 1],
        colors: [LandingColors.tealDark, LandingColors.teal, Color(0xFF0A8A80)],
      ),
      child: Column(
        children: [
          SectionHeading(
            tag: LocaleKeys.landingPrivacyTag,
            title: LocaleKeys.landingPrivacyTitle,
            onDark: true,
          ),
          const SizedBox(height: 52),
          ResponsiveGrid(
            desktopColumns: 4,
            minItemWidth: 250,
            children: _items
                .map(
                  (item) => PrivacyTrustCard(
                    icon: item.$1,
                    title: item.$2,
                    body: item.$3,
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }
}
