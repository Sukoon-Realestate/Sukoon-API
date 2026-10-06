import 'package:flutter/material.dart';

/// Local, resolution-independent sample interior. Never presented as a listing photo.
class PropertyIllustration extends StatelessWidget {
  const PropertyIllustration({required this.tint, super.key});
  final Color tint;

  @override
  Widget build(BuildContext context) => ExcludeSemantics(
    child: CustomPaint(painter: _InteriorPainter(tint), size: Size.infinite),
  );
}

class _InteriorPainter extends CustomPainter {
  const _InteriorPainter(this.tint);
  final Color tint;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(size.width / 320, size.height / 180);
    void rect(double x, double y, double w, double h, Color c, [double r = 0]) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(Rect.fromLTWH(x, y, w, h), Radius.circular(r)),
        Paint()..color = c,
      );
    }

    final wall = Color.lerp(tint, const Color(0xFFF9F6ED), .7)!;
    final fabric = Color.lerp(tint, const Color(0xFF315D4F), .65)!;
    rect(0, 0, 320, 180, wall);
    rect(0, 132, 320, 48, const Color(0xFFD7C5A9));
    rect(0, 129, 320, 4, const Color(0xFFF9F6ED));
    // Window and soft daylight.
    rect(32, 18, 88, 99, const Color(0xFFFFFFFF), 2);
    rect(38, 24, 76, 87, const Color(0xFFCEE1DD));
    rect(74, 24, 3, 87, Colors.white);
    rect(38, 65, 76, 3, Colors.white);
    canvas.drawPath(
      Path()
        ..moveTo(38, 111)
        ..lineTo(114, 111)
        ..lineTo(212, 166)
        ..lineTo(79, 166)
        ..close(),
      Paint()..color = Colors.white.withValues(alpha: .24),
    );
    // Framed artwork.
    rect(168, 23, 40, 48, const Color(0xFFA18B6B), 1);
    rect(172, 27, 32, 40, const Color(0xFFF7F2E5));
    canvas.drawCircle(const Offset(188, 43), 10, Paint()..color = tint);
    rect(178, 48, 20, 14, fabric, 10);
    // Rug, sofa, cushions and legs.
    canvas.drawOval(
      const Rect.fromLTWH(102, 143, 175, 27),
      Paint()..color = const Color(0xFFEFE8D9),
    );
    rect(141, 116, 5, 30, const Color(0xFF665D4D), 2);
    rect(256, 116, 5, 30, const Color(0xFF665D4D), 2);
    rect(139, 88, 126, 49, fabric, 10);
    rect(147, 92, 50, 29, Color.lerp(fabric, Colors.white, .16)!, 7);
    rect(202, 92, 53, 29, Color.lerp(fabric, Colors.white, .12)!, 7);
    rect(134, 112, 136, 26, fabric, 6);
    rect(152, 98, 22, 23, const Color(0xFFE8D8B7), 5);
    // Coffee table and plant.
    rect(165, 148, 5, 18, const Color(0xFF836D52), 2);
    rect(213, 148, 5, 18, const Color(0xFF836D52), 2);
    rect(153, 144, 79, 7, const Color(0xFFA68A63), 5);
    rect(187, 137, 16, 7, const Color(0xFFF9F6ED), 2);
    rect(49, 121, 22, 27, const Color(0xFFB38E70), 5);
    rect(58, 86, 3, 39, fabric);
    for (var i = 0; i < 3; i++) {
      canvas.drawOval(
        Rect.fromLTWH(40 + i * 6, 84 - i * 8, 20, 13),
        Paint()..color = fabric,
      );
      canvas.drawOval(
        Rect.fromLTWH(59, 87 - i * 9, 19, 12),
        Paint()..color = Color.lerp(fabric, Colors.white, .15)!,
      );
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _InteriorPainter oldDelegate) =>
      oldDelegate.tint != tint;
}
