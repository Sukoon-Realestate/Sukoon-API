import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import '../phone_mockup/phone_mockup.dart';
import '../shared/scroll_reveal.dart';

class HeroPhones extends StatelessWidget {
  const HeroPhones({required this.phoneWidth, super.key});
  final double phoneWidth;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: phoneWidth * 2.45,
      height: phoneWidth * 2.8,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Positioned.fill(
            top: 28,
            bottom: 24,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: LandingColors.tealDark,
                borderRadius: BorderRadius.circular(160),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF287F69), LandingColors.tealDark],
                ),
              ),
            ),
          ),
          Positioned.fill(
            top: 50,
            bottom: 50,
            child: DecoratedBox(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white.withValues(alpha: .13)),
              ),
            ),
          ),
          Positioned(
            left: phoneWidth * .12,
            top: phoneWidth * .42,
            child: ScrollReveal(
              delay: 180,
              child: Transform.rotate(
                angle: -.09,
                child: PhoneMockup(
                  audience: Audience.owner,
                  width: phoneWidth * .88,
                ),
              ),
            ),
          ),
          Positioned(
            right: phoneWidth * .12,
            top: phoneWidth * .2,
            child: ScrollReveal(
              delay: 320,
              child: Transform.rotate(
                angle: .06,
                child: PhoneMockup(
                  audience: Audience.tenant,
                  width: phoneWidth,
                ),
              ),
            ),
          ),
          Positioned(
            bottom: 0,
            child: ScrollReveal(
              delay: 440,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 18,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: LandingColors.border),
                  boxShadow: [
                    BoxShadow(
                      color: LandingColors.teal.withValues(alpha: .12),
                      blurRadius: 30,
                      offset: const Offset(0, 12),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.event_available_rounded,
                      color: LandingColors.teal,
                    ),
                    const SizedBox(width: 10),
                    Text(
                      LocaleKeys.landingTrustOrganizedVisitsTitle,
                      style: const TextStyle(
                        color: LandingColors.navy,
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
