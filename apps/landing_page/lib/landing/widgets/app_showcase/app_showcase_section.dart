import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import '../phone_mockup/phone_mockup.dart';
import '../shared/imports.dart';
import 'demo_video_card.dart';

class AppShowcaseSection extends StatefulWidget {
  const AppShowcaseSection({super.key});
  @override
  State<AppShowcaseSection> createState() => _AppShowcaseSectionState();
}

class _AppShowcaseSectionState extends State<AppShowcaseSection> {
  Audience _audience = Audience.tenant;

  @override
  Widget build(BuildContext context) {
    final tenant = _audience == Audience.tenant;
    final reduced = MediaQuery.disableAnimationsOf(context);
    return SectionSpacing(
      backgroundColor: const Color(0xFFEDF3ED),
      child: Column(
        children: [
          SectionHeading(
            tag: LocaleKeys.landingAppTag,
            title: LocaleKeys.landingAppSectionTitle,
            subtitle: LocaleKeys.landingPreviewDisclaimer,
          ),
          const SizedBox(height: 28),
          const DemoVideoCard(),
          const SizedBox(height: 40),
          AudienceToggle(
            value: _audience,
            onChanged: (value) => setState(() => _audience = value),
          ),
          const SizedBox(height: 40),
          LayoutBuilder(
            builder: (context, constraints) {
              final copy = ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 430),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      tenant
                          ? Icons.travel_explore_rounded
                          : Icons.space_dashboard_outlined,
                      color: LandingColors.teal,
                      size: 36,
                    ),
                    const SizedBox(height: 20),
                    Text(
                      tenant
                          ? LocaleKeys.landingTenantHomePreviewLabel
                          : LocaleKeys.landingOwnerDashboardPreviewLabel,
                      style: const TextStyle(
                        fontSize: 30,
                        fontWeight: FontWeight.w800,
                        color: LandingColors.navy,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      tenant
                          ? LocaleKeys.landingTenantPreviewBody
                          : LocaleKeys.landingOwnerPreviewBody,
                      style: const TextStyle(
                        fontSize: 17,
                        height: 1.8,
                        color: LandingColors.subtext,
                      ),
                    ),
                    const SizedBox(height: 24),
                    for (final item
                        in (tenant
                                ? LandingContent.tenantSteps
                                : LandingContent.ownerSteps)
                            .take(3))
                      Padding(
                        padding: const EdgeInsets.only(bottom: 16),
                        child: Row(
                          children: [
                            Text(
                              item.number,
                              style: const TextStyle(
                                color: LandingColors.teal,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Text(
                                item.title,
                                style: const TextStyle(
                                  color: LandingColors.navy,
                                  fontSize: 16,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              );
              final phone = AnimatedSwitcher(
                duration: Duration(milliseconds: reduced ? 0 : 420),
                switchInCurve: Curves.easeOutCubic,
                transitionBuilder: (child, animation) => FadeTransition(
                  opacity: animation,
                  child: SlideTransition(
                    position: Tween(
                      begin: const Offset(.08, 0),
                      end: Offset.zero,
                    ).animate(animation),
                    child: child,
                  ),
                ),
                child: PhoneMockup(
                  key: ValueKey(_audience),
                  audience: _audience,
                  width: 220,
                ),
              );
              if (constraints.maxWidth < 760) {
                return Column(
                  children: [copy, const SizedBox(height: 30), phone],
                );
              }
              return Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  Flexible(child: copy),
                  const SizedBox(width: 48),
                  phone,
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}
