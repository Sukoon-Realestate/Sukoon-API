import 'package:flutter/material.dart';

class PhoneSideButton extends StatelessWidget {
  const PhoneSideButton({
    required this.top,
    required this.width,
    required this.height,
    this.left,
    this.right,
    super.key,
  });

  final double? left;
  final double? right;
  final double top;
  final double width;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: left,
      right: right,
      top: top,
      width: width,
      height: height,
      child: const DecoratedBox(
        decoration: BoxDecoration(
          color: Color(0xFF2A2A2C),
          borderRadius: BorderRadius.all(Radius.circular(2)),
        ),
      ),
    );
  }
}
