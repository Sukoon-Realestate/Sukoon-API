import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../data/models/chat_content.dart';
import 'shared/chat_participant_avatar.dart';

class ChatCard extends StatelessWidget {
  const ChatCard({super.key, required this.conversation});

  final ConversationContent conversation;

  @override
  Widget build(BuildContext context) {
    return Row(
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
                  Expanded(
                    child: AppText(
                      conversation.name,
                      color: AppColors.sokoonNavy,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w700,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (conversation.isVerified) ...[
                    6.szW,
                    Tooltip(
                      message: LocaleKeys.verified,
                      child: Icon(
                        Icons.verified_rounded,
                        color: AppColors.sokoonTeal,
                        size: 18.r,
                      ),
                    ),
                  ],
                ],
              ),
              4.szH,
              AppText(
                _displayTime(context),
                color: AppColors.sokoonGray,
                fontSize: 11.sp,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              if (conversation.property.isNotEmpty) ...[
                2.szH,
                AppText(
                  conversation.property,
                  color: AppColors.sokoonGray,
                  fontSize: 12.sp,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
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
    ).paddingSymmetric(horizontal: 20.w, vertical: 14.h);
  }

  String _displayTime(BuildContext context) {
    final DateTime? value = conversation.lastMessageAt?.toLocal();
    if (value == null) return conversation.time;
    final DateTime now = DateTime.now();
    final MaterialLocalizations localizations = MaterialLocalizations.of(
      context,
    );
    if (value.year == now.year &&
        value.month == now.month &&
        value.day == now.day) {
      return localizations.formatTimeOfDay(TimeOfDay.fromDateTime(value));
    }
    return localizations.formatShortDate(value);
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
          ChatParticipantAvatar(
            name: conversation.name,
            avatarUrl: conversation.otherParticipant.avatarUrl,
            size: 48.r,
          ),
          if (conversation.unreadCount > 0)
            PositionedDirectional(
              top: -4.h,
              end: -4.w,
              child: Container(
                constraints: BoxConstraints(minWidth: 20.r, minHeight: 20.r),
                padding: EdgeInsets.all(4.r),
                alignment: Alignment.center,
                decoration: const BoxDecoration(
                  color: AppColors.red,
                  borderRadius: BorderRadius.all(Radius.circular(20)),
                ),
                child: AppText(
                  conversation.unreadCount > 99
                      ? '99+'
                      : '${conversation.unreadCount}',
                  color: AppColors.white,
                  fontSize: 10.sp,
                  fontWeight: FontWeight.w700,
                  textAlign: TextAlign.center,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
