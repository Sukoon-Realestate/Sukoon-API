import 'package:flutter/material.dart';

/// Opt-in sizing for apps that let controls grow with accessibility text.
@immutable
class AppControlTheme extends ThemeExtension<AppControlTheme> {
  const AppControlTheme({this.minimumHeight = 48, this.radius = 12});

  final double minimumHeight;
  final double radius;

  @override
  AppControlTheme copyWith({double? minimumHeight, double? radius}) =>
      AppControlTheme(
        minimumHeight: minimumHeight ?? this.minimumHeight,
        radius: radius ?? this.radius,
      );

  @override
  AppControlTheme lerp(covariant AppControlTheme? other, double t) =>
      other == null
      ? this
      : AppControlTheme(
          minimumHeight:
              minimumHeight + (other.minimumHeight - minimumHeight) * t,
          radius: radius + (other.radius - radius) * t,
        );
}
