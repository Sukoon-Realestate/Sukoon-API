import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';

class CarouselButton extends StatelessWidget {
  const CarouselButton({
    required this.tooltip,
    required this.icon,
    required this.foreground,
    required this.background,
    required this.onPressed,
    this.borderColor,
    super.key,
  });

  final String tooltip;
  final IconData icon;
  final Color foreground;
  final Color background;
  final Color? borderColor;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final enabled = onPressed != null;

    return Tooltip(
      message: tooltip,
      child: Material(
        color: enabled ? background : LandingColors.softSurface,
        shape: CircleBorder(
          side: BorderSide(
            color: borderColor ?? Colors.transparent,
            width: 1.5,
          ),
        ),
        child: InkWell(
          onTap: onPressed,
          customBorder: const CircleBorder(),
          child: SizedBox(
            width: 44,
            height: 44,
            child: Icon(
              icon,
              color: enabled
                  ? foreground
                  : LandingColors.subtext.withValues(alpha: 0.45),
            ),
          ),
        ),
      ),
    );
  }
}
