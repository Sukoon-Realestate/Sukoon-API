import 'package:flutter/material.dart';

class SocialButton extends StatelessWidget {
  const SocialButton({required this.icon, required this.tooltip, super.key});

  final IconData icon;
  final String tooltip;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: Material(
        color: Colors.white.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(10),
        child: InkWell(
          onTap: () {},
          borderRadius: BorderRadius.circular(10),
          child: Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, size: 18, color: Colors.white),
          ),
        ),
      ),
    );
  }
}
