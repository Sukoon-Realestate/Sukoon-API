import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../config/res/config_imports.dart';

class AppText extends StatelessWidget {
  final bool withIcon;
  final String text;
  final Color? color;
  final double? fontSize;
  final FontWeight? _fontWeight;

  /// Base typography. Individual styling arguments override this style.
  final TextStyle? style;
  final TextAlign textAlign;
  final TextOverflow? overflow;
  final int? maxLines;
  final double? height;
  final TextDecoration? decoration;

  FontWeight get fontWeight =>
      _fontWeight ?? style?.fontWeight ?? FontWeight.normal;

  const AppText(
    this.text, {
    super.key,
    this.icon,
    this.color,
    this.withIcon = false,
    this.decoration,
    this.fontSize,
    FontWeight? fontWeight,
    this.style,
    this.overflow,
    this.textAlign = TextAlign.start,
    this.maxLines,
    this.height,
  }) : _fontWeight = fontWeight;

  final Widget? icon;
  const AppText.withIcon({
    super.key,
    required this.icon,
    required this.text,
    this.decoration,
    this.withIcon = true,
    this.color,
    this.fontSize,
    FontWeight? fontWeight,
    this.style,
    this.textAlign = TextAlign.start,
    this.overflow,
    this.maxLines,
    this.height,
  }) : _fontWeight = fontWeight;

  @override
  Widget build(BuildContext context) {
    final TextStyle effectiveStyle = style == null
        ? TextStyle(
            decoration: decoration,
            color: color,
            fontSize: fontSize ?? (withIcon ? FontSize.s16 : null),
            fontWeight: fontWeight,
            height: height,
            fontFamily: ConstantManager.fontFamily,
          )
        : style!.copyWith(
            decoration: decoration,
            color: color,
            fontSize:
                fontSize ?? (withIcon ? style!.fontSize ?? FontSize.s16 : null),
            fontWeight: _fontWeight,
            height: height,
          );
    switch (withIcon) {
      case true:
        return Row(
          spacing: 5.w,
          children: [
            icon!,
            Text(
              text,
              textAlign: textAlign,
              overflow: overflow,
              maxLines: maxLines,
              style: effectiveStyle,
            ),
          ],
        );
      default:
        return Text(
          text,
          textAlign: textAlign,
          overflow: overflow,
          maxLines: maxLines,
          style: effectiveStyle,
        );
    }
  }
}
