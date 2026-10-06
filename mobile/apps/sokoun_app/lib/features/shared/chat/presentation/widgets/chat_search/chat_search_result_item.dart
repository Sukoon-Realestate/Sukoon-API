import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_screen.dart';

import '../shared/chat_participant_avatar.dart';

class ChatSearchResultItem extends StatelessWidget {
  const ChatSearchResultItem({super.key, required this.conversation});

  final ConversationContent conversation;

  void _openConversation() {
    Go.to(ChatScreen(conversation: conversation));
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: _openConversation,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: 12.w,
        children: [
          ChatParticipantAvatar(
            name: conversation.name,
            avatarUrl: conversation.otherParticipant.avatarUrl,
            size: 40.r,
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: AppText(
                        conversation.name,
                        style: AppTextStyles.bold14.copyWith(
                          color: context.appColor(AppColors.sokoonNavy),
                          fontSize: 14.sp,
                          height: 1.45,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    AppText(
                      conversation.time,
                      style: AppTextStyles.regular11.copyWith(
                        color: context.appColor(AppColors.sokoonGray),
                        fontSize: 11.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                    ),
                  ],
                ),
                2.szH,
                AppText(
                  conversation.property,
                  style: AppTextStyles.regular12.copyWith(
                    color: context.appColor(AppColors.sokoonGray),
                    fontSize: 12.sp,
                    height: 1.45,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                3.szH,
                AppText(
                  conversation.lastMessage,
                  style: AppTextStyles.regular12.copyWith(
                    color: context.appColor(AppColors.sokoonTeal),
                    fontSize: 12.sp,
                    height: 1.45,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ).paddingSymmetric(vertical: 12.h),
    );
  }
}
