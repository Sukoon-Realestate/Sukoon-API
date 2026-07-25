import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/chat/data/models/chat_content.dart';

import '../shared/chat_verified_badge.dart';

class ChatListItem extends StatelessWidget {
  const ChatListItem({
    super.key,
    required this.conversation,
    required this.onPressed,
  });

  final ConversationContent conversation;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      key: ValueKey('chat-${conversation.id}'),
      onTap: onPressed,
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 14.h),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _ConversationAvatar(conversation: conversation),
            12.szW,
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: AppText(
                          conversation.name,
                          color: AppColors.sokoonNavy,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w900,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (conversation.isVerified) ...[
                        6.szW,
                        const ChatVerifiedBadge(),
                      ],
                      const Spacer(),
                      AppText(
                        conversation.time,
                        color: AppColors.sokoonGray,
                        fontSize: 11.sp,
                        fontWeight: FontWeight.w400,
                        maxLines: 1,
                      ),
                    ],
                  ),
                  2.szH,
                  AppText(
                    conversation.property,
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  3.szH,
                  AppText(
                    conversation.lastMessage,
                    color: conversation.unreadCount > 0
                        ? AppColors.sokoonNavy
                        : AppColors.sokoonMuted,
                    fontSize: 12.sp,
                    fontWeight: conversation.unreadCount > 0
                        ? FontWeight.w700
                        : FontWeight.w400,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConversationAvatar extends StatelessWidget {
  const _ConversationAvatar({required this.conversation});

  final ConversationContent conversation;

  @override
  Widget build(BuildContext context) {
    return SizedBox.square(
      dimension: 48.r,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          DecoratedBox(
            decoration: const BoxDecoration(
              color: AppColors.mintLight,
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Icon(
                Icons.person_outline_rounded,
                color: AppColors.sokoonTeal,
                size: 23.r,
              ),
            ),
          ),
          if (conversation.unreadCount > 0)
            PositionedDirectional(
              top: -4.h,
              end: -4.w,
              child: Container(
                width: 20.r,
                height: 20.r,
                alignment: Alignment.center,
                decoration: const BoxDecoration(
                  color: AppColors.red,
                  shape: BoxShape.circle,
                ),
                child: AppText(
                  '${conversation.unreadCount}',
                  color: AppColors.white,
                  fontSize: 10.sp,
                  fontWeight: FontWeight.w900,
                  textAlign: TextAlign.center,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
