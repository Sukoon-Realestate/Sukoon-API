import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/visits/imports.dart';

import 'owner_visit_request_action_row.dart';

class OwnerVisitRequestCard extends StatelessWidget {
  const OwnerVisitRequestCard({
    super.key,
    required this.request,
    required this.onPressed,
    required this.onChatPressed,
    required this.onAcceptPressed,
    required this.onRejectPressed,
  });

  final OwnerVisitRequestContent request;
  final VoidCallback onPressed;
  final VoidCallback onChatPressed;
  final VoidCallback onAcceptPressed;
  final VoidCallback onRejectPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        key: ValueKey('owner-request-card-${request.id}'),
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16.r),
        child: Container(
          padding: EdgeInsets.all(15.w),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(color: AppColors.grayPale),
          ),
          child: Column(
            children: [
              Row(
                textDirection: TextDirection.ltr,
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
                    ),
                  ),
                  10.szW,
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
                              const OwnerVerifiedBadge(),
                            ],
                          ],
                        ),
                        4.szH,
                        AppText(
                          request.property,
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
                  IconButton(
                    key: ValueKey('owner-request-chat-${request.id}'),
                    onPressed: onChatPressed,
                    visualDensity: VisualDensity.compact,
                    style: IconButton.styleFrom(
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
                ],
              ),
              12.szH,
              _VisitTimeRow(time: request.time),
              if (request.status.canDecide) ...[
                12.szH,
                OwnerVisitRequestActionRow(
                  onAcceptPressed: onAcceptPressed,
                  onRejectPressed: onRejectPressed,
                ),
              ],
              if (!request.status.canDecide) ...[
                12.szH,
                _RequestStatusBanner(status: request.status),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _VisitTimeRow extends StatelessWidget {
  const _VisitTimeRow({required this.time});

  final String time;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 8.h),
      decoration: BoxDecoration(
        color: AppColors.grayOffWhite,
        borderRadius: BorderRadius.circular(10.r),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Icon(
            Icons.calendar_today_outlined,
            color: AppColors.sokoonGray,
            size: 15.r,
          ),
          7.szW,
          AppText(
            time,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w400,
          ),
        ],
      ),
    );
  }
}

class _RequestStatusBanner extends StatelessWidget {
  const _RequestStatusBanner({required this.status});

  final OwnerVisitRequestStatus status;

  Color get _backgroundColor {
    if (status.isAccepted) {
      return AppColors.greenPale;
    }
    if (status.isRejected) {
      return AppColors.redPale;
    }
    return AppColors.grayBackground;
  }

  Color get _foregroundColor {
    if (status.isAccepted) {
      return AppColors.green;
    }
    if (status.isRejected) {
      return AppColors.red;
    }
    return AppColors.sokoonGray;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 40.h,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: _backgroundColor,
        borderRadius: BorderRadius.circular(10.r),
        border: Border.all(color: _foregroundColor.withValues(alpha: 0.2)),
      ),
      child: AppText(
        status.label,
        color: _foregroundColor,
        fontSize: 13.sp,
        fontWeight: FontWeight.w700,
      ),
    );
  }
}
