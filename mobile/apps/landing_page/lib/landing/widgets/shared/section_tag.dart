import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';

class SectionTag extends StatelessWidget {
  const SectionTag({
    required this.text,
    super.key,
    this.color = LandingColors.teal,
    this.onDark = false,
  });

  final String text;
  final Color color;
  final bool onDark;

  @override
  Widget build(BuildContext context) {
    final effectiveColor = onDark ? Colors.white : color;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
      decoration: BoxDecoration(
        color: effectiveColor.withValues(alpha: onDark ? 0.15 : 0.07),
        border: Border.all(
          color: effectiveColor.withValues(alpha: onDark ? 0.25 : 0.16),
        ),
        borderRadius: BorderRadius.circular(100),
      ),
      child: FittedBox(
        fit: BoxFit.scaleDown,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                color: effectiveColor,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              text,
              style: TextStyle(
                color: effectiveColor,
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
