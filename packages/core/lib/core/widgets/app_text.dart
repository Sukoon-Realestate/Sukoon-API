import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../config/res/config_imports.dart';

class AppText extends StatelessWidget {
  final bool withIcon;
  final String text;
  final Color? color;
  final double? fontSize;
  final FontWeight fontWeight;
  final TextAlign textAlign;
  final TextOverflow? overflow;
  final int? maxLines;
  final double? height;
  final TextDecoration? decoration;

  const AppText(
      this.text, {
        super.key, this.icon,
        this.color, this.withIcon = false,
        this.decoration,
        this.fontSize,
        this.fontWeight = FontWeight.normal,
        this.overflow,
        this.textAlign = TextAlign.start,
        this.maxLines,
        this.height,
      });

  final Widget? icon;
  const AppText.withIcon({
    super.key,
    required this.icon,
    required this.text,
    this.decoration,
    this.withIcon = true,
    this.color,
    this.fontSize,
    this.fontWeight = FontWeight.normal,
    this.textAlign = TextAlign.start,
    this.overflow,
    this.maxLines,
    this.height
  });

  @override
  Widget build(BuildContext context) {
    switch(withIcon){
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
              style: TextStyle(
                decoration: decoration,
                color: color,
                fontSize: fontSize ?? FontSize.s16,
                fontWeight: fontWeight,
                height: height,
              ),
            ),
          ],
        );
      default:
        return Text(
          text,
          textAlign: textAlign,
          overflow: overflow,
          maxLines: maxLines,
          style: TextStyle(
            color: color,
            fontSize: fontSize,
            fontWeight: fontWeight,
              decoration: decoration,
            height: height,
            fontFamily: ConstantManager.fontFamily
          ),
        );
    }

  }
}
