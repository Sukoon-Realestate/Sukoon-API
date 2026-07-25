import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/chat/data/models/chat_content.dart';

import '../shared/chat_verified_badge.dart';

class ChatThreadHeader extends StatelessWidget {
  const ChatThreadHeader({
    super.key,
    required this.conversation,
    required this.onBackPressed,
    required this.onReportPressed,
  });

  final ConversationContent conversation;
  final VoidCallback onBackPressed;
  final VoidCallback onReportPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(14.w, 8.h, 14.w, 12.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        children: [
          IconButton(
            key: const ValueKey('chat-thread-back'),
            onPressed: onBackPressed,
            visualDensity: VisualDensity.compact,
            icon: Icon(
              Icons.arrow_back_ios_new_rounded,
              color: AppColors.sokoonNavy,
              size: 18.r,
            ),
          ),
          Container(
            width: 38.r,
            height: 38.r,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: AppColors.mintLight,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.person_outline_rounded,
              color: AppColors.sokoonTeal,
              size: 18.r,
            ),
          ),
          10.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  conversation.name,
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w900,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                2.szH,
                AppText(
                  '${conversation.property} · ${LocaleKeys.chatActiveNow}',
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          if (conversation.isVerified) ...[const ChatVerifiedBadge(), 4.szW],
          IconButton(
            key: const ValueKey('chat-report-action'),
            tooltip: LocaleKeys.chatReportProblemTitle,
            onPressed: onReportPressed,
            visualDensity: VisualDensity.compact,
            icon: Icon(
              Icons.more_vert_rounded,
              color: AppColors.sokoonGray,
              size: 20.r,
            ),
          ),
        ],
      ),
    );
  }
}
