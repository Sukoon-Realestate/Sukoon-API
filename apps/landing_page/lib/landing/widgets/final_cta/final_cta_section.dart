import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import '../shared/imports.dart';
import 'sokoon_logo_mark.dart';
import 'store_badge.dart';

class FinalCtaSection extends StatelessWidget {
  const FinalCtaSection({required this.onNavigate, super.key});

  final ValueChanged<String> onNavigate;

  @override
  Widget build(BuildContext context) {
    return SectionSpacing(
      backgroundColor: const Color(0xFFF0FDFA),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 700),
          child: Column(
            children: [
              Container(
                width: 72,
                height: 72,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: LandingColors.teal.withValues(alpha: 0.09),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const SokoonLogoMark(),
              ),
              const SizedBox(height: 24),
              Text(
                LocaleKeys.landingFinalTitle,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: LandingColors.navy,
                  fontSize: 44,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                LocaleKeys.landingFinalBody,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: LandingColors.subtext,
                  fontSize: 17,
                  height: 1.7,
                ),
              ),
              const SizedBox(height: 36),
              Wrap(
                alignment: WrapAlignment.center,
                spacing: 16,
                runSpacing: 12,
                children: [
                  LandingButton(
                    label: LocaleKeys.landingStartAsTenant,
                    onPressed: () => onNavigate('hero'),
                    height: 56,
                    horizontalPadding: 32,
                    radius: 16,
                  ),
                  LandingButton(
                    label: LocaleKeys.landingStartAsOwner,
                    onPressed: () => onNavigate('hero'),
                    backgroundColor: LandingColors.gold,
                    height: 56,
                    horizontalPadding: 32,
                    radius: 16,
                  ),
                ],
              ),
              const SizedBox(height: 40),
              Wrap(
                alignment: WrapAlignment.center,
                spacing: 14,
                runSpacing: 12,
                children: [
                  StoreBadge(
                    icon: Icons.apple_rounded,
                    label: LocaleKeys.landingAppStore,
                  ),
                  StoreBadge(
                    icon: Icons.play_arrow_rounded,
                    label: LocaleKeys.landingGooglePlay,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
