import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../shared/sokoon_logo.dart';

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
      ],
    );
  }
}
