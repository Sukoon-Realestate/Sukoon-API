import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';
import 'section_tag.dart';

class SectionHeading extends StatelessWidget {
  const SectionHeading({
    required this.tag,
    required this.title,
    super.key,
    this.subtitle,
    this.onDark = false,
  });

  final String tag;
  final String title;
  final String? subtitle;
  final bool onDark;

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final titleSize = LandingBreakpoints.isMobile(width) ? 30.0 : 44.0;
    return Column(
      children: [
        SectionTag(text: tag, onDark: onDark),
        const SizedBox(height: 16),
        Text(
          title,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: onDark ? Colors.white : LandingColors.navy,
            fontSize: titleSize,
            fontWeight: FontWeight.w900,
            height: 1.25,
          ),
        ),
        if (subtitle != null) ...[
          const SizedBox(height: 14),
          Text(
            subtitle!,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: onDark
                  ? Colors.white.withValues(alpha: 0.72)
                  : LandingColors.subtext,
              fontSize: 16,
              height: 1.6,
            ),
          ),
        ],
      ],
    );
  }
}
