import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';

class TenantChatComposer extends StatelessWidget {
  const TenantChatComposer({
    super.key,
    required this.controller,
    required this.onAttachmentPressed,
    required this.onVoicePressed,
    required this.onSendPressed,
  });

  final TextEditingController controller;
  final VoidCallback onAttachmentPressed;
  final VoidCallback onVoicePressed;
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
          children: [
            _ComposerActionButton(
              key: const ValueKey('tenant-chat-send'),
              onPressed: onSendPressed,
              backgroundColor: AppColors.sokoonTeal,
              icon: Icons.send_rounded,
              iconColor: AppColors.white,
            ),
            8.szW,
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
                    IconButton(
                      key: const ValueKey('tenant-chat-voice'),
                      onPressed: onVoicePressed,
                      visualDensity: VisualDensity.compact,
                      padding: EdgeInsets.zero,
                      icon: Icon(
                        Icons.mic_none_rounded,
                        color: AppColors.sokoonGray,
                        size: 18.r,
                      ),
                    ),
                    Expanded(
                      child: TextField(
                        key: const ValueKey('tenant-chat-message-field'),
                        controller: controller,
                        minLines: 1,
                        maxLines: 4,
                        textDirection: TextDirection.rtl,
                        textInputAction: TextInputAction.send,
                        onSubmitted: (_) => onSendPressed(),
                        style: TextStyle(
                          color: AppColors.sokoonNavy,
                          fontSize: 14.sp,
                          fontFamily: ConstantManager.fontFamily,
                        ),
                        decoration: InputDecoration(
                          hintText: LocaleKeys.chatMessageHint,
                          hintStyle: TextStyle(
                            color: AppColors.sokoonMuted,
                            fontSize: 14.sp,
                            fontFamily: ConstantManager.fontFamily,
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
            8.szW,
            _ComposerActionButton(
              key: const ValueKey('tenant-chat-attachment'),
              onPressed: onAttachmentPressed,
              backgroundColor: AppColors.scaffoldBackground,
              icon: Icons.image_outlined,
              iconColor: AppColors.sokoonGray,
            ),
          ],
        ),
      ),
    );
  }
}

class _ComposerActionButton extends StatelessWidget {
  const _ComposerActionButton({
    super.key,
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
    return SizedBox.square(
      dimension: 38.r,
      child: Material(
        color: backgroundColor,
        shape: const CircleBorder(),
        child: InkWell(
          onTap: onPressed,
          customBorder: const CircleBorder(),
          child: Icon(icon, color: iconColor, size: 18.r),
        ),
      ),
    );
  }
}
