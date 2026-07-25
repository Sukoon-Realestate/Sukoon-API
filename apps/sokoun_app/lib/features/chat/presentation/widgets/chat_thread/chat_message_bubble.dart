import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
      key: ValueKey('chat-message-${message.message.id}'),
      constraints: BoxConstraints(maxWidth: 285.w),
      margin: EdgeInsets.only(bottom: 8.h),
      child: Column(
        crossAxisAlignment: isFromMe
            ? CrossAxisAlignment.end
            : CrossAxisAlignment.start,
        children: [
          Container(
            padding: EdgeInsets.symmetric(
              horizontal: _isVoice ? 14.w : 16.w,
              vertical: _isVoice ? 11.h : 10.h,
            ),
            decoration: BoxDecoration(
              color: isFromMe ? AppColors.white : AppColors.sokoonTeal,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(isFromMe ? 4.r : 16.r),
                topRight: Radius.circular(isFromMe ? 16.r : 4.r),
                bottomLeft: Radius.circular(16.r),
                bottomRight: Radius.circular(16.r),
              ),
              border: isFromMe
                  ? Border.all(color: AppColors.sokoonBorder)
                  : null,
            ),
            child: _isVoice
                ? _VoiceMessageContent(
                    duration: message.message.body,
                    isFromMe: isFromMe,
                  )
                : AppText(
                    message.message.body,
                    color: isFromMe ? AppColors.sokoonNavy : AppColors.white,
                    fontSize: 14.sp,
                    height: 1.4,
                    maxLines: 8,
                  ),
          ),
          3.szH,
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 4.w),
            child: AppText(
              message.time ?? '',
              color: AppColors.sokoonGray,
              fontSize: 10.sp,
              maxLines: 1,
            ),
          ),
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
    final Color foreground = isFromMe ? AppColors.sokoonTeal : AppColors.white;

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
          color: foreground.withValues(alpha: .8),
          fontSize: 11.sp,
          maxLines: 1,
        ),
      ],
    );
  }
}
