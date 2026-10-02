import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import 'package:melos_core/core/widgets/app_logo_widget.dart';

class SokoonLogo extends StatelessWidget {
  const SokoonLogo({super.key, this.size = 38, this.light = false});

  final double size;
  final bool light;

  @override
  Widget build(BuildContext context) {
    final foreground = light ? Colors.white : LandingColors.navy;
    final secondary = light
        ? Colors.white.withValues(alpha: 0.5)
        : LandingColors.subtext;

    return Semantics(
      label: LocaleKeys.landingLogoSemanticLabel,
      image: true,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          AppLogoWidget(size: size),
          const SizedBox(width: 10),
          Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                LocaleKeys.landingAppTitle,
                style: TextStyle(
                  color: foreground,
                  fontSize: size * 0.54,
                  fontWeight: FontWeight.w900,
                  height: 0.95,
                ),
              ),
              Text(
                LocaleKeys.landingLogoLatinName,
                textDirection: TextDirection.ltr,
                style: TextStyle(
                  color: secondary,
                  fontSize: size * 0.31,
                  fontWeight: FontWeight.w600,
                  height: 1.1,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
