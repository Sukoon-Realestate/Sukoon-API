import 'package:flutter/material.dart';

import '../../../../Helper/Interfaces/helper_imports.dart';

class SizeAnimationOptions extends AnimationOption {
  final double begin;
  final double end;
  final Axis axis;
  final double axisAlignment;
  final Alignment alignment;
  const SizeAnimationOptions({
    this.axis = Axis.vertical,
    this.alignment = Alignment.center,
    this.axisAlignment = 0.0,
    this.begin = 0.0,
    this.end = 1.0,
    super.duration,
    super.curve,
    super.reverseCurve,
    super.reverseDuration,
    super.secondaryTransition,
  });
}
