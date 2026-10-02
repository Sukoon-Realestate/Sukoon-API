import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/start_conversation_screen.dart';

class OwnerVisitRequestIdentityRow extends StatelessWidget {
  const OwnerVisitRequestIdentityRow({super.key, required this.request});

  final OwnerVisitRequestContent request;

  void _openChat() {
    if (request.tenantId.isEmpty) return;
    Go.to(StartConversationScreen(userId: request.tenantId));
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        OwnerTenantAvatar(
          name: request.name,
          initial: request.initial,
          avatarUrl: request.avatar,
        ),
        10.szW,
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 3.h,
            children: [
              Row(
                spacing: 6.w,
                children: [
                  Flexible(
                    child: AppText(
                      request.name,
                      style: AppTextStyles.bold14.copyWith(
                        color: AppColors.sokoonNavy,
                        fontSize: 14.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (request.isVerified) const OwnerVerifiedBadge(),
                ],
              ),
              AppText(
                request.subtitle.trim().isNotEmpty
                    ? request.subtitle
                    : request.property,
                style: AppTextStyles.regular11.copyWith(
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  height: 1.45,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
        8.szW,
        Semantics(
          button: true,
          label: LocaleKeys.ownerVisitOpenChat,
          child: SizedBox.square(
            dimension: 48.r,
            child: IconButton(
              tooltip: LocaleKeys.ownerVisitOpenChat,
              onPressed: request.canChat ? _openChat : null,
              padding: EdgeInsets.zero,
              visualDensity: VisualDensity.compact,
              style: IconButton.styleFrom(
                minimumSize: Size.square(48.r),
                maximumSize: Size.square(48.r),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                backgroundColor: AppColors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10.r),
                  side: const BorderSide(color: AppColors.grayPale),
                ),
              ),
              icon: Icon(
                Icons.chat_bubble_outline_rounded,
                color: AppColors.sokoonTeal,
                size: 16.r,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
