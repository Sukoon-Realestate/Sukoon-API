import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

class SplashLogoSheen extends StatelessWidget {
  const SplashLogoSheen({
    super.key,
    required this.progress,
    required this.child,
  });

  final Animation<double> progress;
  final Widget child;

  @override
  Widget build(BuildContext context) =>
      CustomPaint(foregroundPainter: _LogoSheenPainter(progress), child: child);
}

class _LogoSheenPainter extends CustomPainter {
  _LogoSheenPainter(this.progress) : super(repaint: progress);

  final Animation<double> progress;

  @override
  void paint(Canvas canvas, Size size) {
    final double value = progress.value;
    if (value <= 0 || value >= 1) return;

    // The supplied 640px logo includes mint padding. Keep the light on the
    // rounded teal mark so its baked-in background stays seamless.
    final Rect mark = Rect.fromLTRB(
      size.width * 84 / 640,
      size.height * 116 / 640,
      size.width * 556 / 640,
      size.height * 520 / 640,
    );
    final double center = size.width * (-.4 + 1.8 * value);
    final Rect sweep = Rect.fromLTWH(
      center - size.width * .22,
      0,
      size.width * .44,
      size.height,
    );
    final Paint paint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          AppColors.transparent,
          AppColors.white.withValues(alpha: .13 * math.sin(math.pi * value)),
          AppColors.transparent,
        ],
      ).createShader(sweep);

    canvas.save();
    canvas.clipRRect(
      RRect.fromRectAndRadius(mark, Radius.circular(size.width * 132 / 640)),
    );
    canvas.drawRect(Offset.zero & size, paint);
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _LogoSheenPainter oldDelegate) =>
      oldDelegate.progress != progress;
}
