import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import '../shared/imports.dart';
import 'journey_step_card.dart';

class HowItWorksSection extends StatelessWidget {
  const HowItWorksSection({
    required this.audience,
    required this.onAudienceChanged,
    super.key,
  });
  final Audience audience;
  final ValueChanged<Audience> onAudienceChanged;

  @override
  Widget build(BuildContext context) {
    final color = audience == Audience.tenant
        ? LandingColors.teal
        : LandingColors.gold;
    final steps = audience == Audience.tenant
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
            value: audience,
            compactLabels: true,
            onChanged: onAudienceChanged,
          ),
          const SizedBox(height: 48),
          AnimatedSwitcher(
            duration: Duration(
              milliseconds: MediaQuery.disableAnimationsOf(context) ? 0 : 350,
            ),
            child: ResponsiveGrid(
              key: ValueKey(audience),
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
