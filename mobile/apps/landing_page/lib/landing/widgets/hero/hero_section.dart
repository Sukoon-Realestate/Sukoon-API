import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';
import '../shared/site_content.dart';
import 'hero_content.dart';
import '../shared/scroll_reveal.dart';
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
        final content = ScrollReveal(
          child: HeroContent(centered: !desktop, onNavigate: onNavigate),
        );
        final phones = HeroPhones(
          phoneWidth: desktop
              ? 190
              : (mobile ? (constraints.maxWidth - 40) / 2.45 : 175),
        );

        return Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topRight,
              end: Alignment.bottomLeft,
              stops: [0, 0.5, 1],
              colors: [
                Color(0xFFEDF5ED),
                LandingColors.background,
                Color(0xFFF7F1E4),
              ],
            ),
          ),
          child: Stack(
            children: [
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
