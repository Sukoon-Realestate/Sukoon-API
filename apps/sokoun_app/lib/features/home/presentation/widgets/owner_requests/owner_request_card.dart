import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_request_content.dart';

import 'owner_request_action_button.dart';
import 'owner_request_privacy_banner.dart';
import 'owner_request_status_chip.dart';
import 'owner_request_verified_badge.dart';

class OwnerRequestCard extends StatelessWidget {
  const OwnerRequestCard({super.key, required this.request});

  final OwnerRequestContent request;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(20.r),
        border: Border.all(color: AppColors.sokoonBorder),
        boxShadow: const [
          BoxShadow(
            color: AppColors.shadowBlack04,
            blurRadius: 4,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            textDirection: TextDirection.ltr,
            children: [
              Container(
                width: 42.r,
                height: 42.r,
                decoration: const BoxDecoration(
                  color: AppColors.bluePale,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.person_outline_rounded,
                  color: AppColors.blue,
                  size: 21.r,
                ),
              ),
              12.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
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
                          const OwnerRequestVerifiedBadge(),
                        ],
                      ],
                    ),
                    3.szH,
                    AppText(
                      request.details,
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w400,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              8.szW,
              OwnerRequestStatusChip(status: request.status),
            ],
          ),
          if (request.showActions) ...[
            14.szH,
            Row(
              textDirection: TextDirection.ltr,
              children: [
                for (
                  int index = 0;
                  index < OwnerRequestsContent.actions.length;
                  index++
                ) ...[
                  OwnerRequestActionButton(
                    action: OwnerRequestsContent.actions[index],
                  ),
                  if (index < OwnerRequestsContent.actions.length - 1) 8.szW,
                ],
              ],
            ),
          ],
          if (request.privacyMessage != null) ...[
            14.szH,
            OwnerRequestPrivacyBanner(message: request.privacyMessage!),
          ],
        ],
      ),
    );
  }
}
