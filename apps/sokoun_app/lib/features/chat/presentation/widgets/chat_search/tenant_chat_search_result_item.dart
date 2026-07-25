import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/chat/data/models/tenant_chat_content.dart';

class TenantChatSearchResultItem extends StatelessWidget {
  const TenantChatSearchResultItem({
    super.key,
    required this.conversation,
    required this.onPressed,
  });

  final TenantConversationContent conversation;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      key: ValueKey('tenant-chat-search-result-${conversation.id}'),
      onTap: onPressed,
      child: Padding(
        padding: EdgeInsets.symmetric(vertical: 12.h),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 40.r,
              height: 40.r,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                color: AppColors.mintLight,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.person_outline_rounded,
                color: AppColors.sokoonTeal,
                size: 19.r,
              ),
            ),
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
                          fontWeight: FontWeight.w900,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      AppText(
                        conversation.time,
                        color: AppColors.sokoonGray,
                        fontSize: 11.sp,
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
                    color: AppColors.sokoonTeal,
                    fontSize: 12.sp,
                    maxLines: 2,
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
