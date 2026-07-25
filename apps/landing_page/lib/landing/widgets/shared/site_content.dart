import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';

class SiteContent extends StatelessWidget {
  const SiteContent({
    required this.child,
    super.key,
    this.maxWidth = LandingBreakpoints.contentMaxWidth,
  });

  final Widget child;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: SizedBox(width: double.infinity, child: child),
      ),
    );
  }
}
