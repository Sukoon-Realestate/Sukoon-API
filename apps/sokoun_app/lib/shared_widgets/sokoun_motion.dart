import 'package:flutter/material.dart';

abstract final class SokounMotion {
  static Duration duration(BuildContext context, {int milliseconds = 200}) =>
      MediaQuery.disableAnimationsOf(context) ||
          MediaQuery.accessibleNavigationOf(context)
      ? Duration.zero
      : Duration(milliseconds: milliseconds);

  static const Curve curve = Curves.easeOutCubic;
}
