import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import '../shared/imports.dart';

class HeroContent extends StatelessWidget {
  const HeroContent({
    required this.centered,
    required this.onNavigate,
    super.key,
  });

  final bool centered;
  final ValueChanged<String> onNavigate;

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final mobile = LandingBreakpoints.isMobile(width);
    final titleSize = mobile
        ? 39.0
        : width < 1000
        ? 50.0
        : 60.0;
    final crossAxisAlignment = centered
        ? CrossAxisAlignment.center
        : CrossAxisAlignment.start;
    final textAlign = centered ? TextAlign.center : TextAlign.start;

    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 610),
      child: Column(
        crossAxisAlignment: crossAxisAlignment,
        children: [
          SectionTag(text: LocaleKeys.landingHeroTag),
          const SizedBox(height: 16),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(text: '${LocaleKeys.landingHeroTitle}\n'),
                TextSpan(
                  text: LocaleKeys.landingHeroTitleAccent,
                  style: const TextStyle(color: LandingColors.teal),
                ),
              ],
            ),
            textAlign: textAlign,
            style: TextStyle(
              color: LandingColors.navy,
              fontSize: titleSize,
              fontWeight: FontWeight.w900,
              height: 1.18,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            LocaleKeys.landingHeroDescription,
            textAlign: textAlign,
            style: TextStyle(
              color: LandingColors.subtext,
              fontSize: mobile ? 17 : 18,
              height: 1.8,
            ),
          ),
          const SizedBox(height: 32),
          Wrap(
            alignment: centered ? WrapAlignment.center : WrapAlignment.start,
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: 14,
            runSpacing: 12,
            children: [
              LandingButton(
                label: LocaleKeys.landingSearchHousing,
                icon: Icons.search_rounded,
                onPressed: () => onNavigate('tenant'),
              ),
              LandingButton(
                label: LocaleKeys.landingListProperty,
                onPressed: () => onNavigate('owner'),
                backgroundColor: Colors.white,
                foregroundColor: LandingColors.navy,
                borderColor: LandingColors.border,
              ),
              TextButton(
                onPressed: () => onNavigate('properties'),
                style: TextButton.styleFrom(
                  foregroundColor: LandingColors.teal,
                ),
                child: Text(
                  LocaleKeys.landingBrowseAsGuest,
                  style: const TextStyle(
                    decoration: TextDecoration.underline,
                    decorationColor: LandingColors.teal,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
