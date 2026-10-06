import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import '../shared/imports.dart';
import 'property_card.dart';

class PropertyShowcaseSection extends StatelessWidget {
  const PropertyShowcaseSection({required this.onExplore, super.key});

  final VoidCallback onExplore;

  @override
  Widget build(BuildContext context) {
    return SectionSpacing(
      backgroundColor: Colors.white,
      child: Column(
        children: [
          SectionHeading(
            tag: LocaleKeys.landingPropertiesTag,
            title: LocaleKeys.landingPropertiesTitle,
            subtitle: LocaleKeys.landingPropertiesBody,
          ),
          const SizedBox(height: 52),
          ResponsiveGrid(
            desktopColumns: 4,
            minItemWidth: 260,
            spacing: 24,
            runSpacing: 24,
            children: LandingContent.properties
                .map(
                  (property) =>
                      PropertyCard(property: property, onDetails: onExplore),
                )
                .toList(),
          ),
          const SizedBox(height: 40),
          LandingButton(
            label: LocaleKeys.landingExploreProperties,
            onPressed: onExplore,
            backgroundColor: Colors.white,
            foregroundColor: LandingColors.teal,
            borderColor: LandingColors.teal,
            horizontalPadding: 32,
          ),
        ],
      ),
    );
  }
}
