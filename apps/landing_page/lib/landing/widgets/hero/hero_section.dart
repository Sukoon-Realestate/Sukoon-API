import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';
import '../shared/site_content.dart';
import 'hero_content.dart';
import 'hero_phones.dart';

class HeroSection extends StatelessWidget {
  const HeroSection({required this.onNavigate, super.key});

  final ValueChanged<String> onNavigate;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final desktop = constraints.maxWidth >= 1000;
        final mobile = LandingBreakpoints.isMobile(constraints.maxWidth);
        final content = HeroContent(centered: !desktop, onNavigate: onNavigate);
        final phones = HeroPhones(
          phoneWidth: desktop ? 202 : (mobile ? 138 : 175),
        );

        return Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topRight,
              end: Alignment.bottomLeft,
              stops: [0, 0.5, 1],
              colors: [
                Color(0xFFF0FDFA),
                LandingColors.background,
                Color(0xFFFEF9F0),
              ],
            ),
          ),
          child: Stack(
            children: [
              const Positioned(
                top: -70,
                left: 38,
                child: Icon(
                  Icons.home_rounded,
                  size: 390,
                  color: Color(0x0F0F766E),
                ),
              ),
              Positioned(
                bottom: -80,
                right: 28,
                child: Container(
                  width: 260,
                  height: 260,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: LandingColors.teal.withValues(alpha: 0.05),
                      width: 38,
                    ),
                  ),
                ),
              ),
              Padding(
                padding: EdgeInsets.fromLTRB(
                  mobile ? 20 : 24,
                  mobile ? 48 : 80,
                  mobile ? 20 : 24,
                  mobile ? 42 : 60,
                ),
                child: SiteContent(
                  child: desktop
                      ? Row(
                          children: [
                            Expanded(child: content),
                            const SizedBox(width: 48),
                            phones,
                          ],
                        )
                      : Column(
                          children: [
                            content,
                            SizedBox(height: mobile ? 46 : 58),
                            phones,
                          ],
                        ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
