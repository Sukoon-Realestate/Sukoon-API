import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/validators.dart';

class ChatComposer extends StatelessWidget {
  const ChatComposer({
    super.key,
    required this.controller,
    required this.onSendPressed,
  });

  final TextEditingController controller;
  final VoidCallback onSendPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 11.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          spacing: 8.w,
          children: [
            _ComposerActionButton(
              onPressed: onSendPressed,
              backgroundColor: AppColors.sokoonTeal,
              icon: Icons.send_rounded,
              iconColor: AppColors.white,
            ),
            Expanded(
              child: Container(
                constraints: BoxConstraints(minHeight: 40.h),
                padding: EdgeInsets.symmetric(horizontal: 10.w),
                decoration: BoxDecoration(
                  color: AppColors.scaffoldBackground,
                  borderRadius: BorderRadius.circular(16.r),
                  border: Border.all(color: AppColors.sokoonBorder),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: controller,
                        maxLength: Validators.chatMessageMaxLength,
                        buildCounter:
                            (
                              _, {
                              required currentLength,
                              required isFocused,
                              maxLength,
                            }) => null,
                        minLines: 1,
                        maxLines: 4,
                        textInputAction: TextInputAction.send,
                        onEditingComplete: onSendPressed,
                        style: AppTextStyles.base.copyWith(
                          color: AppColors.sokoonNavy,
                          fontSize: 14.sp,
                        ),
                        decoration: InputDecoration(
                          hintText: LocaleKeys.chatMessageHint,
                          hintStyle: AppTextStyles.base.copyWith(
                            color: AppColors.sokoonMuted,
                            fontSize: 14.sp,
                          ),
                          border: InputBorder.none,
                          isDense: true,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ComposerActionButton extends StatelessWidget {
  const _ComposerActionButton({
    required this.onPressed,
    required this.backgroundColor,
    required this.icon,
    required this.iconColor,
  });

  final VoidCallback onPressed;
  final Color backgroundColor;
  final IconData icon;
  final Color iconColor;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: LocaleKeys.chatSendMessage,
      child: SizedBox.square(
        dimension: 44.r,
        child: Material(
          color: backgroundColor,
          shape: const CircleBorder(),
          child: InkWell(
            onTap: onPressed,
            customBorder: const CircleBorder(),
            child: Icon(icon, color: iconColor, size: 18.r),
          ),
        ),
      ),
    );
  }
}
