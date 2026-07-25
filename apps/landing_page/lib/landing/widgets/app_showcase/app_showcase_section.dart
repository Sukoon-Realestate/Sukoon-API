import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import '../phone_mockup/phone_mockup.dart';
import '../shared/imports.dart';
import 'carousel_button.dart';

class AppShowcaseSection extends StatefulWidget {
  const AppShowcaseSection({super.key});

  @override
  State<AppShowcaseSection> createState() => _AppShowcaseSectionState();
}

class _AppShowcaseSectionState extends State<AppShowcaseSection> {
  static List<(String, Audience)> get _screens => [
    (LocaleKeys.landingTenantHomePreviewLabel, Audience.tenant),
    (LocaleKeys.landingOwnerDashboardPreviewLabel, Audience.owner),
    (LocaleKeys.landingTenantHomePreviewLabel, Audience.tenant),
    (LocaleKeys.landingOwnerDashboardPreviewLabel, Audience.owner),
  ];

  var _index = 0;

  void _setIndex(int value) {
    setState(() => _index = value.clamp(0, _screens.length - 1));
  }

  @override
  Widget build(BuildContext context) {
    final mobile = LandingBreakpoints.isMobile(
      MediaQuery.sizeOf(context).width,
    );
    final visible = <int>[
      if (!mobile && _index > 0) _index - 1,
      _index,
      if (!mobile && _index < _screens.length - 1) _index + 1,
    ];

    return SectionSpacing(
      backgroundColor: LandingColors.background,
      child: Column(
        children: [
          SectionHeading(
            tag: LocaleKeys.landingAppTag,
            title: LocaleKeys.landingAppSectionTitle,
          ),
          const SizedBox(height: 52),
          Row(
            textDirection: TextDirection.ltr,
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: visible.map((screenIndex) {
              final active = screenIndex == _index;

              return Padding(
                padding: EdgeInsets.symmetric(horizontal: mobile ? 0 : 16),
                child: GestureDetector(
                  onTap: () => _setIndex(screenIndex),
                  child: AnimatedOpacity(
                    duration: const Duration(milliseconds: 300),
                    opacity: active ? 1 : 0.48,
                    child: AnimatedScale(
                      duration: const Duration(milliseconds: 300),
                      scale: active ? 1 : 0.78,
                      child: PhoneMockup(
                        audience: _screens[screenIndex].$2,
                        width: 182,
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 32),
          Text(
            _screens[_index].$1,
            style: const TextStyle(
              color: LandingColors.navy,
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              _screens.length,
              (index) => GestureDetector(
                onTap: () => _setIndex(index),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  width: index == _index ? 24 : 8,
                  height: 8,
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  decoration: BoxDecoration(
                    color: index == _index
                        ? LandingColors.teal
                        : LandingColors.border,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Row(
            textDirection: TextDirection.ltr,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CarouselButton(
                tooltip: LocaleKeys.landingPreviousScreen,
                icon: Icons.chevron_left_rounded,
                foreground: LandingColors.navy,
                background: Colors.white,
                borderColor: LandingColors.border,
                onPressed: _index == 0 ? null : () => _setIndex(_index - 1),
              ),
              const SizedBox(width: 16),
              CarouselButton(
                tooltip: LocaleKeys.landingNextScreen,
                icon: Icons.chevron_right_rounded,
                foreground: Colors.white,
                background: LandingColors.teal,
                onPressed: _index == _screens.length - 1
                    ? null
                    : () => _setIndex(_index + 1),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
