import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../../data/models/chat_content.dart';
import '../shared/chat_participant_avatar.dart';
import '../shared/chat_verified_badge.dart';

class ChatParticipantTitle extends StatelessWidget {
  const ChatParticipantTitle({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      ChatParticipantAvatar(
        name: conversation.name,
        avatarUrl: conversation.otherParticipant.avatarUrl,
        size: 38.r,
      ),
      SizedBox(width: 10.w),
      Expanded(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppText(
              conversation.name,
              style: AppTextStyles.bold14.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 14.sp,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            if (conversation.property.isNotEmpty || conversation.isOnline)
              AppText(
                [
                  conversation.property,
                  if (conversation.isOnline) LocaleKeys.chatActiveNow,
                ].where((value) => value.isNotEmpty).join(' · '),
                style: AppTextStyles.regular11.copyWith(
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
          ],
        ),
      ),
      if (conversation.isVerified) const ChatVerifiedBadge(),
    ],
  );
}
