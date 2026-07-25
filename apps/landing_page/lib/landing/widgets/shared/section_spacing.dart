import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';
import 'site_content.dart';

class SectionSpacing extends StatelessWidget {
  const SectionSpacing({
    required this.child,
    super.key,
    this.backgroundColor,
    this.gradient,
    this.verticalPadding = 80,
    this.horizontalPadding = 24,
  });

  final Widget child;
  final Color? backgroundColor;
  final Gradient? gradient;
  final double verticalPadding;
  final double horizontalPadding;

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final mobile = LandingBreakpoints.isMobile(width);

    return DecoratedBox(
      decoration: BoxDecoration(color: backgroundColor, gradient: gradient),
      child: Padding(
        padding: EdgeInsets.symmetric(
          horizontal: mobile ? 20 : horizontalPadding,
          vertical: mobile ? verticalPadding * 0.7 : verticalPadding,
        ),
        child: SiteContent(child: child),
      ),
    );
  }
}
