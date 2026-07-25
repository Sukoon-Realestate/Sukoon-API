import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import '../shared/imports.dart';
import 'feature_card.dart';

class AudienceFeaturesSection extends StatelessWidget {
  const AudienceFeaturesSection({
    required this.audience,
    required this.onAudienceChanged,
    required this.onCtaPressed,
    super.key,
  });

  final Audience audience;
  final ValueChanged<Audience> onAudienceChanged;
  final VoidCallback onCtaPressed;

  @override
  Widget build(BuildContext context) {
    final tenant = audience == Audience.tenant;
    final color = tenant ? LandingColors.teal : LandingColors.gold;
    final features = tenant
        ? LandingContent.tenantFeatures
        : LandingContent.ownerFeatures;

    return SectionSpacing(
      child: Column(
        children: [
          SectionHeading(
            tag: LocaleKeys.landingFeaturesTag,
            title: LocaleKeys.landingFeaturesTitle,
          ),
          const SizedBox(height: 24),
          AudienceToggle(value: audience, onChanged: onAudienceChanged),
          const SizedBox(height: 38),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: Column(
              key: ValueKey(audience),
              children: [
                Text(
                  tenant
                      ? LocaleKeys.landingTenantFeaturesTitle
                      : LocaleKeys.landingOwnerFeaturesTitle,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: LandingColors.navy,
                    fontSize: 28,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  tenant
                      ? LocaleKeys.landingTenantFeaturesBody
                      : LocaleKeys.landingOwnerFeaturesBody,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: LandingColors.subtext,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 38),
                ResponsiveGrid(
                  desktopColumns: 3,
                  tabletColumns: 2,
                  minItemWidth: 280,
                  children: features
                      .map(
                        (feature) =>
                            FeatureCard(feature: feature, color: color),
                      )
                      .toList(),
                ),
              ],
            ),
          ),
          const SizedBox(height: 40),
          LandingButton(
            label: tenant
                ? LocaleKeys.landingStartTenantSearch
                : LocaleKeys.landingStartListingProperty,
            onPressed: onCtaPressed,
            backgroundColor: color,
            horizontalPadding: 32,
          ),
        ],
      ),
    );
  }
}
