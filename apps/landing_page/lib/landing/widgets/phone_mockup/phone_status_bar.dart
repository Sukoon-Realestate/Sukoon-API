import 'package:flutter/material.dart';

class PhoneStatusBar extends StatelessWidget {
  const PhoneStatusBar({required this.color, super.key});

  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 35,
      color: color,
      padding: const EdgeInsets.symmetric(horizontal: 13),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Text(
            '9:41',
            textDirection: TextDirection.ltr,
            style: TextStyle(
              color: Colors.white,
              fontSize: 9,
              fontWeight: FontWeight.w700,
            ),
          ),
          Row(
            children: List.generate(
              3,
              (_) => Container(
                width: 4,
                height: 4,
                margin: const EdgeInsets.only(left: 3),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.8),
                  shape: BoxShape.circle,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
