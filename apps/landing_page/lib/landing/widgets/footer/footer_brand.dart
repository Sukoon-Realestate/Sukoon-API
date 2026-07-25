import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../shared/sokoon_logo.dart';
import 'social_button.dart';

class FooterBrand extends StatelessWidget {
  const FooterBrand({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SokoonLogo(size: 40, light: true),
        const SizedBox(height: 16),
        Text(
          LocaleKeys.landingFooterBody,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.55),
            fontSize: 14,
            height: 1.8,
          ),
        ),
        const SizedBox(height: 20),
        Row(
          children: [
            SocialButton(
              icon: Icons.facebook_rounded,
              tooltip: LocaleKeys.landingFacebook,
            ),
            const SizedBox(width: 10),
            SocialButton(
              icon: Icons.camera_alt_outlined,
              tooltip: LocaleKeys.landingInstagram,
            ),
            const SizedBox(width: 10),
            SocialButton(
              icon: Icons.work_outline,
              tooltip: LocaleKeys.landingLinkedin,
            ),
          ],
        ),
      ],
    );
  }
}
