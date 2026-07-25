import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';

class LandingButton extends StatefulWidget {
  const LandingButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.backgroundColor = LandingColors.teal,
    this.foregroundColor = Colors.white,
    this.borderColor,
    this.icon,
    this.height = 52,
    this.horizontalPadding = 28,
    this.radius = 14,
  });

  final String label;
  final VoidCallback onPressed;
  final Color backgroundColor;
  final Color foregroundColor;
  final Color? borderColor;
  final IconData? icon;
  final double height;
  final double horizontalPadding;
  final double radius;

  @override
  State<LandingButton> createState() => _LandingButtonState();
}

class _LandingButtonState extends State<LandingButton> {
  var _hovering = false;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: widget.label,
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        onEnter: (_) => setState(() => _hovering = true),
        onExit: (_) => setState(() => _hovering = false),
        child: AnimatedScale(
          scale: _hovering ? 1.015 : 1,
          duration: const Duration(milliseconds: 150),
          child: Material(
            color: widget.backgroundColor,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(widget.radius),
              side: widget.borderColor == null
                  ? BorderSide.none
                  : BorderSide(color: widget.borderColor!, width: 1.5),
            ),
            child: InkWell(
              onTap: widget.onPressed,
              borderRadius: BorderRadius.circular(widget.radius),
              child: Padding(
                padding: EdgeInsets.symmetric(
                  horizontal: widget.horizontalPadding,
                ),
                child: SizedBox(
                  height: widget.height,
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (widget.icon != null) ...[
                          Icon(
                            widget.icon,
                            color: widget.foregroundColor,
                            size: 19,
                          ),
                          const SizedBox(width: 9),
                        ],
                        Text(
                          widget.label,
                          style: TextStyle(
                            color: widget.foregroundColor,
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
