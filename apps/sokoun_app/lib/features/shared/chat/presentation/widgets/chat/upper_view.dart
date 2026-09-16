import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';

import '../shared/chat_participant_avatar.dart';
import '../shared/chat_verified_badge.dart';

class ChatThreadHeader extends StatelessWidget {
  const ChatThreadHeader({
    super.key,
    required this.conversation,
    required this.onReportPressed,
  });

  final ConversationContent conversation;
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
            onPressed: Go.back,
            visualDensity: VisualDensity.compact,
            icon: Icon(
              Icons.arrow_back_ios_new_rounded,
              color: AppColors.sokoonNavy,
              size: 18.r,
            ),
          ),
          ChatParticipantAvatar(
            name: conversation.name,
            avatarUrl: conversation.otherParticipant.avatarUrl,
            size: 38.r,
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
                if (conversation.property.isNotEmpty ||
                    conversation.isOnline) ...[
                  2.szH,
                  AppText(
                    [
                      conversation.property,
                      if (conversation.isOnline) LocaleKeys.chatActiveNow,
                    ].where((value) => value.isNotEmpty).join(' · '),
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),
          if (conversation.isVerified) ...[const ChatVerifiedBadge(), 4.szW],
          IconButton(
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

class ChatUpperWidget extends ChatThreadHeader {
  const ChatUpperWidget({
    super.key,
    required super.conversation,
    required super.onReportPressed,
  });
}
