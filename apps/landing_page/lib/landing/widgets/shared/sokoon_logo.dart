import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';

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
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              color: LandingColors.teal,
              borderRadius: BorderRadius.circular(size * 0.36),
            ),
            padding: EdgeInsets.all(size * 0.16),
            child: CustomPaint(painter: _SokoonMarkPainter()),
          ),
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

class _SokoonMarkPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final white = Paint()..color = Colors.white;
    final teal = Paint()..color = LandingColors.teal;
    final path = Path()
      ..moveTo(size.width * 0.5, size.height * 0.06)
      ..lineTo(size.width, size.height * 0.45)
      ..lineTo(size.width * 0.86, size.height * 0.45)
      ..lineTo(size.width * 0.86, size.height)
      ..lineTo(size.width * 0.14, size.height)
      ..lineTo(size.width * 0.14, size.height * 0.45)
      ..lineTo(0, size.height * 0.45)
      ..close();
    canvas.drawPath(path, white);

    final windowRadius = Radius.circular(size.width * 0.035);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(
          size.width * 0.24,
          size.height * 0.58,
          size.width * 0.18,
          size.height * 0.13,
        ),
        windowRadius,
      ),
      teal,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(
          size.width * 0.58,
          size.height * 0.58,
          size.width * 0.18,
          size.height * 0.13,
        ),
        windowRadius,
      ),
      teal,
    );

    final door = Path()
      ..moveTo(size.width * 0.36, size.height)
      ..lineTo(size.width * 0.36, size.height * 0.82)
      ..quadraticBezierTo(
        size.width * 0.5,
        size.height * 0.68,
        size.width * 0.64,
        size.height * 0.82,
      )
      ..lineTo(size.width * 0.64, size.height)
      ..close();
    canvas.drawPath(door, teal);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
