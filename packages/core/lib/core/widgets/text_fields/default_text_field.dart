import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../config/res/config_imports.dart';
import '../app_text.dart';
import '../buttons/app_control_theme.dart';

enum TitleStatus { withTitle, withoutTitle }

class DefaultTextField extends StatefulWidget {
  final double? borderRadius;
  final TitleStatus withTitle;
  final String? title;
  final bool secure;
  final TextInputType inputType;
  final TextEditingController? controller;
  final FormFieldValidator<String?>? validator;
  final String? label;
  final Function(String?)? onSubmitted;
  final Color? fillColor;
  final Widget? prefixIcon;
  final bool readOnly;
  final bool filled;
  final int? maxLength;
  final TextAlign? textAlign;
  final TextDirection? textDirection;
  final EdgeInsetsGeometry? contentPadding;
  final GestureTapCallback? onTap;
  final String? suffixText;
  final TextInputAction action;
  final bool autoFocus;
  final FocusNode? focusNode;
  final Widget? prefixWidget;
  final List<TextInputFormatter>? inputFormatters;
  final Widget? suffixIcon;
  final bool? isPassword;
  final int? maxLines;
  final int? minLines;
  final bool? hasBorderColor;
  final Color? borderColor;
  final void Function(String?)? onChanged;
  final bool closeWhenTapOutSide;
  final TextStyle? style;
  final String? upperTitle;

  const DefaultTextField({
    super.key,
    this.title,
    this.borderRadius,
    this.secure = false,
    this.inputType = TextInputType.text,
    this.borderColor,
    this.onTap,
    this.controller,
    this.contentPadding,
    this.closeWhenTapOutSide = true,
    this.hasBorderColor = true,
    this.validator,
    this.label,
    this.onSubmitted,
    this.isPassword = false,
    this.fillColor,
    this.inputFormatters,
    this.prefixIcon,
    this.prefixWidget,
    this.maxLength,
    this.filled = true,
    this.readOnly = false,
    this.textAlign = TextAlign.start,
    this.textDirection,
    this.action = TextInputAction.next,
    this.focusNode,
    this.autoFocus = false,
    this.suffixText,
    this.suffixIcon,
    this.maxLines,
    this.minLines,
    this.onChanged,
    this.style,
  }) : upperTitle = null,
       withTitle = TitleStatus.withoutTitle;

  const DefaultTextField.withTitle({
    super.key,
    this.title,
    this.borderRadius,
    this.secure = false,
    this.inputType = TextInputType.text,
    this.borderColor,
    this.onTap,
    this.controller,
    this.contentPadding,
    this.closeWhenTapOutSide = true,
    this.hasBorderColor = true,
    this.validator,
    this.label,
    this.onSubmitted,
    this.isPassword = false,
    this.fillColor,
    this.inputFormatters,
    this.prefixIcon,
    this.prefixWidget,
    this.maxLength,
    this.filled = true,
    this.readOnly = false,
    this.textAlign = TextAlign.start,
    this.textDirection,
    this.action = TextInputAction.next,
    this.focusNode,
    this.autoFocus = false,
    this.suffixText,
    this.suffixIcon,
    this.maxLines,
    this.minLines,
    this.onChanged,
    this.style,
    required this.upperTitle,
  }) : withTitle = TitleStatus.withTitle;

  @override
  State<DefaultTextField> createState() => _DefaultTextFieldState();
}

class _DefaultTextFieldState extends State<DefaultTextField> {
  late final ValueNotifier<bool> _isSecure;

  @override
  void initState() {
    super.initState();
    _isSecure = ValueNotifier(widget.isPassword == true);
  }

  @override
  void dispose() {
    _isSecure.dispose();
    super.dispose();
  }

  void _debounce(String val) {
    // EasyDebounce.debounce(
    //   'text_field_${widget.hashCode}', // unique key
    //   const Duration(milliseconds: 200),
    //       () => widget.onChanged?.call(val),
    // );
    widget.onChanged?.call(val);
  }

  @override
  Widget build(BuildContext context) {
    final bool isLabel = widget.label != null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      spacing: 5.h,
      children: [
        if (widget.withTitle == TitleStatus.withTitle)
          AppText(
            widget.upperTitle!,
            fontWeight: FontWeight.w500,
            fontSize: Theme.of(context).extension<AppControlTheme>() == null
                ? 11.sp
                : 14.sp,
          ),

        ValueListenableBuilder<bool>(
          valueListenable: _isSecure,
          builder: (context, secure, _) => TextFormField(
            autovalidateMode: AutovalidateMode.onUserInteraction,
            controller: widget.controller,
            onChanged: _debounce,
            inputFormatters: widget.inputFormatters,
            obscureText: widget.isPassword == true ? secure : widget.secure,
            onTap: widget.onTap,
            onTapOutside: (event) {
              if (widget.closeWhenTapOutSide == true) {
                FocusScope.of(context).unfocus();
              }
            },
            keyboardType: widget.inputType,
            autofillHints: _getAutoFillHints(widget.inputType),
            validator: widget.validator,
            maxLength: widget.maxLength,
            readOnly: widget.readOnly,
            textAlign: widget.textAlign!,
            textDirection: widget.textDirection,
            maxLines: widget.inputType == TextInputType.multiline
                ? widget.maxLines ?? 7
                : 1,
            minLines: widget.minLines,
            style: widget.style?.copyWith(
              color: widget.style?.color == null
                  ? null
                  : context.appColor(widget.style!.color!),
            ),
            onFieldSubmitted: widget.onSubmitted,
            textInputAction: widget.action,
            enableSuggestions: false,
            autocorrect: false,
            autofocus: widget.autoFocus,
            focusNode: widget.focusNode,
            cursorColor: context.appColor(AppColors.primary),
            decoration: InputDecoration(
              isDense: true,
              errorMaxLines: 3,
              contentPadding: widget.contentPadding,
              counterText: ConstantManager.emptyText,
              filled: widget.filled,
              suffixText: widget.suffixText,
              prefixIcon: widget.isPassword == true
                  ? const Icon(Icons.lock_outline, color: Colors.grey)
                  : widget.prefixIcon,
              suffixIcon: widget.isPassword == true
                  ? IconButton(
                      onPressed: () => _isSecure.value = !secure,
                      icon: Icon(
                        secure
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                        color: Colors.grey,
                      ),
                    )
                  : widget.suffixIcon,
              prefix: widget.prefixWidget,
              fillColor: context.appColor(
                widget.fillColor ?? AppColors.white,
                surface: true,
              ),
              hintText: widget.title,
              label: isLabel ? Text(widget.label!) : null,
              labelStyle: isLabel
                  ? TextStyle(color: context.appColor(AppColors.primary))
                  : null,
              hintStyle: TextStyle(
                fontSize: 13,
                color: Theme.of(context).extension<AppColorTheme>() == null
                    ? Colors.grey[600]
                    : context.appColor(AppColors.sokoonMuted),
                fontWeight: FontWeight.w300,
                fontFamily: ConstantManager.fontFamily,
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(
                  widget.borderRadius ?? AppCircular.r12,
                ),
                borderSide: widget.hasBorderColor == true
                    ? BorderSide(
                        color: context.appColor(
                          widget.borderColor ?? AppColors.border,
                        ),
                      )
                    : BorderSide.none,
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(
                  widget.borderRadius ?? AppCircular.r12,
                ),
                borderSide: BorderSide(
                  color: context.appColor(AppColors.primary),
                ),
              ),
              errorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(
                  widget.borderRadius ?? AppCircular.r12,
                ),
                borderSide: const BorderSide(color: Colors.red),
              ),
              focusedErrorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(
                  widget.borderRadius ?? AppCircular.r12,
                ),
                borderSide: const BorderSide(color: Colors.red),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

List<String> _getAutoFillHints(TextInputType inputType) {
  if (inputType == TextInputType.emailAddress) {
    return [AutofillHints.email];
  } else if (inputType == TextInputType.datetime) {
    return [AutofillHints.birthday];
  } else if (inputType == TextInputType.phone) {
    return [AutofillHints.telephoneNumber];
  } else if (inputType == TextInputType.url) {
    return [AutofillHints.url];
  }
  return [AutofillHints.name, AutofillHints.username];
}
