part of 'config_imports.dart';

/// Opt-in semantic colors. Brand ink stays white on solid actions and media;
/// white surfaces can independently become dark without changing other apps.
@immutable
class AppColorTheme extends ThemeExtension<AppColorTheme> {
  const AppColorTheme({this.foreground = const {}, this.surfaces = const {}});

  final Map<Color, Color> foreground;
  final Map<Color, Color> surfaces;

  Color resolve(Color color, {bool surface = false}) =>
      (surface ? surfaces : foreground)[color] ?? color;

  @override
  AppColorTheme copyWith({
    Map<Color, Color>? foreground,
    Map<Color, Color>? surfaces,
  }) => AppColorTheme(
    foreground: foreground ?? this.foreground,
    surfaces: surfaces ?? this.surfaces,
  );

  @override
  AppColorTheme lerp(covariant AppColorTheme? other, double t) {
    if (other == null) return this;
    Map<Color, Color> blend(Map<Color, Color> start, Map<Color, Color> end) => {
      for (final color in {...start.keys, ...end.keys})
        color: Color.lerp(start[color] ?? color, end[color] ?? color, t)!,
    };
    return AppColorTheme(
      foreground: blend(foreground, other.foreground),
      surfaces: blend(surfaces, other.surfaces),
    );
  }
}

extension AppColorContext on BuildContext {
  Color appColor(Color color, {bool surface = false}) =>
      Theme.of(
        this,
      ).extension<AppColorTheme>()?.resolve(color, surface: surface) ??
      color;
}
