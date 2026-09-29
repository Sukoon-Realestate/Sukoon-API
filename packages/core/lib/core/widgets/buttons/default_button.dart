import 'package:flutter/material.dart';

import '../../../config/res/config_imports.dart';
import '../../extensions/context_extension.dart';
import 'app_control_theme.dart';

class DefaultButton extends StatelessWidget {
  final String? title;
  final Function()? onTap;
  final Color? textColor;
  final Color? color;
  final Color? borderColor;
  final double borderWidth;
  final BorderRadius? borderRadius;
  final EdgeInsets? margin;
  final EdgeInsetsGeometry? padding;
  final double? width;
  final double? fontSize;
  final double? height;

  /// Allows content to grow vertically when [height] is not provided.
  final double? minHeight;
  final double? elevation;
  final bool? disabled;
  final FontWeight? fontWeight;
  final TextStyle? textStyle;
  final Widget? customChild;
  final bool isFitted;

  const DefaultButton({
    super.key,
    this.title,
    this.onTap,
    this.color,
    this.disabled,
    this.textColor,
    this.borderRadius,
    this.margin,
    this.padding,
    this.borderColor,
    this.borderWidth = 1,
    this.fontSize,
    this.width,
    this.height,
    this.minHeight,
    this.fontWeight,
    this.textStyle,
    this.elevation,
    this.customChild,
    this.isFitted = true,
  });

  Widget get _defaultChild => Text(
    title ?? 'Click!',
    style: textStyle == null
        ? TextStyle(
            color: textColor ?? AppColors.buttonText,
            fontSize: fontSize ?? FontSize.s13,
            fontFamily: ConstantManager.fontFamily,
            fontWeight: fontWeight ?? FontWeightManager.medium,
          )
        : textStyle!.copyWith(
            color: textColor ?? textStyle!.color ?? AppColors.buttonText,
            fontSize: fontSize,
            fontWeight: fontWeight,
          ),
  );

  @override
  Widget build(BuildContext context) {
    final AppControlTheme? controls = Theme.of(
      context,
    ).extension<AppControlTheme>();
    final bool grow = controls != null;
    return SizedBox(
      width: width ?? (grow ? double.infinity : context.width * .9),
      height: grow ? null : height ?? (minHeight == null ? AppSize.sH45 : null),
      child: ConstrainedBox(
        constraints: BoxConstraints(
          minHeight: grow
              ? (height ?? minHeight ?? controls.minimumHeight).clamp(
                  controls.minimumHeight,
                  double.infinity,
                )
              : minHeight ?? 0,
        ),
        child: ElevatedButton(
          onPressed: disabled == true ? null : onTap,
          style: ElevatedButton.styleFrom(
            splashFactory: InkRipple.splashFactory,
            surfaceTintColor: color ?? AppColors.buttonColor,
            foregroundColor: textColor ?? AppColors.buttonText,
            backgroundColor: color ?? AppColors.primary,
            padding: padding,
            shape: RoundedRectangleBorder(
              borderRadius:
                  borderRadius ??
                  BorderRadius.circular(controls?.radius ?? AppCircular.r5),
              side: borderColor != null
                  ? BorderSide(
                      color: borderColor ?? Colors.grey[200]!,
                      width: borderWidth,
                    )
                  : BorderSide.none,
            ),
            elevation: elevation ?? ConstantManager.zeroAsDouble,
          ),
          child: isFitted && !grow
              ? FittedBox(child: customChild ?? _defaultChild)
              : customChild ?? _defaultChild,
        ),
      ),
    );
  }
}
