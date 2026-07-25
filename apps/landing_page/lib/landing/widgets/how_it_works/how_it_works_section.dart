import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import '../shared/imports.dart';
import 'journey_step_card.dart';

class HowItWorksSection extends StatefulWidget {
  const HowItWorksSection({super.key});

  @override
  State<HowItWorksSection> createState() => _HowItWorksSectionState();
}

class _HowItWorksSectionState extends State<HowItWorksSection> {
  var _audience = Audience.tenant;

  @override
  Widget build(BuildContext context) {
    final color = _audience == Audience.tenant
        ? LandingColors.teal
        : LandingColors.gold;
    final steps = _audience == Audience.tenant
        ? LandingContent.tenantSteps
        : LandingContent.ownerSteps;

    return SectionSpacing(
      backgroundColor: const Color(0xFFF8FAFC),
      child: Column(
        children: [
          SectionHeading(
            tag: LocaleKeys.landingHowTag,
            title: LocaleKeys.landingHowTitle,
          ),
          const SizedBox(height: 48),
          AudienceToggle(
            value: _audience,
            compactLabels: true,
            onChanged: (value) => setState(() => _audience = value),
          ),
          const SizedBox(height: 48),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: ResponsiveGrid(
              key: ValueKey(_audience),
              desktopColumns: 4,
              minItemWidth: 220,
              spacing: 24,
              runSpacing: 24,
              children: steps
                  .map((step) => JourneyStepCard(step: step, color: color))
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }
}
