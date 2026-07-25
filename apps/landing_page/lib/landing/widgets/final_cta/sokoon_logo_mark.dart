import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';

class SokoonLogoMark extends StatelessWidget {
  const SokoonLogoMark({super.key});

  @override
  Widget build(BuildContext context) {
    return const Icon(Icons.home_rounded, color: LandingColors.teal, size: 36);
  }
}
