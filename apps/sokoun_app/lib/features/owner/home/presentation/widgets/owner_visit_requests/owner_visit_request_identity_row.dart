import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
      textDirection: TextDirection.rtl,
      children: [
        Container(
          width: 40.r,
          height: 40.r,
          alignment: Alignment.center,
          decoration: const BoxDecoration(
            color: AppColors.tealAlpha13,
            shape: BoxShape.circle,
          ),
          child: AppText(
            request.initial,
            color: AppColors.sokoonTeal,
            fontSize: 16.sp,
            fontWeight: FontWeight.w900,
            maxLines: 1,
          ),
        ),
        10.szW,
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                textDirection: TextDirection.rtl,
                children: [
                  Flexible(
                    child: AppText(
                      request.name,
                      color: AppColors.sokoonNavy,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w900,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (request.isVerified) ...[
                    6.szW,
                    const OwnerVerifiedBadge(),
                  ],
                ],
              ),
              3.szH,
              AppText(
                request.property,
                color: AppColors.sokoonGray,
                fontSize: 11.sp,
                fontWeight: FontWeight.w400,
                maxLines: 1,
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
            dimension: 32.r,
            child: IconButton(
              tooltip: LocaleKeys.ownerVisitOpenChat,
              onPressed: request.tenantId.isEmpty ? null : _openChat,
              padding: EdgeInsets.zero,
              visualDensity: VisualDensity.compact,
              style: IconButton.styleFrom(
                minimumSize: Size.square(32.r),
                maximumSize: Size.square(32.r),
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
