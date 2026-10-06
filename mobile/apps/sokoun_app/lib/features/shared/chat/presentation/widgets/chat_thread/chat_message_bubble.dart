import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';

class ChatMessageBubble extends StatelessWidget {
  const ChatMessageBubble({
    super.key,
    required this.message,
    required this.isFromMe,
  });

  final ChatMessages message;
  final bool isFromMe;

  bool get _isVoice => message.message.type == 'voice';

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(maxWidth: 285.w),
      margin: EdgeInsets.only(bottom: 8.h),
      child: Column(
        crossAxisAlignment: isFromMe
            ? CrossAxisAlignment.end
            : CrossAxisAlignment.start,
        spacing: 3.h,
        children: [
          Container(
            padding: EdgeInsets.symmetric(
              horizontal: _isVoice ? 14.w : 16.w,
              vertical: _isVoice ? 11.h : 10.h,
            ),
            decoration: BoxDecoration(
              color: isFromMe
                  ? context.appColor(AppColors.white, surface: true)
                  : context.appColor(AppColors.sokoonTeal, surface: true),
              borderRadius: BorderRadiusDirectional.only(
                topStart: Radius.circular(isFromMe ? 16.r : 4.r),
                topEnd: Radius.circular(isFromMe ? 4.r : 16.r),
                bottomStart: Radius.circular(16.r),
                bottomEnd: Radius.circular(16.r),
              ),
              border: isFromMe
                  ? Border.all(color: context.appColor(AppColors.sokoonBorder))
                  : null,
            ),
            child: _isVoice
                ? _VoiceMessageContent(
                    duration: message.message.body,
                    isFromMe: isFromMe,
                  )
                : AppText(
                    message.message.body,
                    style: AppTextStyles.regular14.copyWith(
                      color: isFromMe
                          ? context.appColor(AppColors.sokoonNavy)
                          : AppColors.white,
                      fontSize: 14.sp,
                      height: 1.4,
                    ),
                  ),
          ),
          AppText(
            message.time ?? '',
            style: AppTextStyles.regular10.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 12.sp,
              height: 1.45,
            ),
            maxLines: 1,
          ).paddingSymmetric(horizontal: 4.w),
        ],
      ),
    );
  }
}

class _VoiceMessageContent extends StatelessWidget {
  const _VoiceMessageContent({required this.duration, required this.isFromMe});

  final String duration;
  final bool isFromMe;

  @override
  Widget build(BuildContext context) {
    final Color foreground = isFromMe
        ? context.appColor(AppColors.sokoonTeal)
        : AppColors.white;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 30.r,
          height: 30.r,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: foreground.withValues(alpha: .18),
            shape: BoxShape.circle,
          ),
          child: Icon(Icons.mic_rounded, color: foreground, size: 16.r),
        ),
        10.szW,
        Row(
          children: [
            for (final double height in const [8, 14, 6, 18, 10, 16, 4, 12])
              Container(
                width: 3.w,
                height: height.h,
                margin: EdgeInsets.symmetric(horizontal: 1.w),
                decoration: BoxDecoration(
                  color: foreground.withValues(alpha: .72),
                  borderRadius: BorderRadius.circular(2.r),
                ),
              ),
          ],
        ),
        8.szW,
        AppText(
          duration,
          style: AppTextStyles.regular11.copyWith(
            color: foreground.withValues(alpha: .8),
            fontSize: 12.sp,
            height: 1.45,
          ),
          maxLines: 1,
        ),
      ],
    );
  }
}
