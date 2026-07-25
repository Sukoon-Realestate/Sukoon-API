import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantChatVoiceRecordingBar extends StatelessWidget {
  const TenantChatVoiceRecordingBar({
    super.key,
    required this.onCancelPressed,
    required this.onSendPressed,
  });

  final VoidCallback onCancelPressed;
  final VoidCallback onSendPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(14.w, 12.h, 14.w, 12.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: SafeArea(
        top: false,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 12.h),
          decoration: BoxDecoration(
            color: AppColors.redPale,
            borderRadius: BorderRadius.circular(16.r),
          ),
          child: Row(
            children: [
              _RecordingButton(
                key: const ValueKey('tenant-chat-voice-send'),
                onPressed: onSendPressed,
                color: AppColors.sokoonTeal,
                icon: Icons.send_rounded,
              ),
              12.szW,
              Expanded(
                child: Row(
                  children: [
                    Container(
                      width: 8.r,
                      height: 8.r,
                      decoration: const BoxDecoration(
                        color: AppColors.red,
                        shape: BoxShape.circle,
                      ),
                    ),
                    6.szW,
                    Flexible(
                      child: AppText(
                        LocaleKeys.chatVoiceRecording,
                        color: AppColors.red,
                        fontSize: 13.sp,
                        fontWeight: FontWeight.w700,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const Spacer(),
                    AppText(
                      '0:24',
                      color: AppColors.sokoonGray,
                      fontSize: 13.sp,
                    ),
                  ],
                ),
              ),
              12.szW,
              _RecordingButton(
                key: const ValueKey('tenant-chat-voice-cancel'),
                onPressed: onCancelPressed,
                color: AppColors.red,
                icon: Icons.close_rounded,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RecordingButton extends StatelessWidget {
  const _RecordingButton({
    super.key,
    required this.onPressed,
    required this.color,
    required this.icon,
  });

  final VoidCallback onPressed;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return SizedBox.square(
      dimension: 42.r,
      child: Material(
        color: color,
        shape: const CircleBorder(),
        child: InkWell(
          onTap: onPressed,
          customBorder: const CircleBorder(),
          child: Icon(icon, color: AppColors.white, size: 19.r),
        ),
      ),
    );
  }
}
