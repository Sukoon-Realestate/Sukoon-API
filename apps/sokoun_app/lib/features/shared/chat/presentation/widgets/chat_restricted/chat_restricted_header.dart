import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/back_button.dart';

import '../../../data/models/chat_content.dart';
import '../shared/chat_participant_avatar.dart';

class ChatRestrictedHeader extends StatelessWidget {
  const ChatRestrictedHeader({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsetsDirectional.fromSTEB(14.w, 8.h, 20.w, 12.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        children: [
          const SokoonBackButton(),
          10.szW,
          ChatParticipantAvatar(
            name: conversation.name,
            avatarUrl: conversation.otherParticipant.avatarUrl,
            size: 38.r,
            backgroundColor: AppColors.grayPale,
            iconColor: AppColors.sokoonMuted,
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
                if (conversation.property.isNotEmpty) ...[
                  2.szH,
                  AppText(
                    conversation.property,
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
