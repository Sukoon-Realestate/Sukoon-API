import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_visit_request_content.dart';

import 'owner_visit_request_action_row.dart';

class OwnerVisitRequestCard extends StatelessWidget {
  const OwnerVisitRequestCard({super.key, required this.request});

  final OwnerVisitRequestContent request;

  @override
  Widget build(BuildContext context) {
    return Container(
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
                          const _VerifiedTag(),
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
              Container(
                width: 32.r,
                height: 32.r,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: AppColors.white,
                  borderRadius: BorderRadius.circular(10.r),
                  border: Border.all(color: AppColors.grayPale),
                ),
                child: Icon(
                  Icons.chat_bubble_outline_rounded,
                  color: AppColors.sokoonGray,
                  size: 16.r,
                ),
              ),
            ],
          ),
          12.szH,
          _VisitTimeRow(time: request.time),
          if (request.showActions) ...[
            12.szH,
            const OwnerVisitRequestActionRow(),
          ],
          if (request.acceptedLabel != null) ...[
            12.szH,
            _AcceptedBanner(label: request.acceptedLabel!),
          ],
        ],
      ),
    );
  }
}

class _VerifiedTag extends StatelessWidget {
  const _VerifiedTag();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: AppColors.tealAlpha07,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: AppText(
        'موثّق',
        color: AppColors.sokoonTeal,
        fontSize: 10.sp,
        fontWeight: FontWeight.w900,
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

class _AcceptedBanner extends StatelessWidget {
  const _AcceptedBanner({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 40.h,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppColors.greenAlpha06,
        borderRadius: BorderRadius.circular(10.r),
        border: Border.all(color: AppColors.greenAlpha19),
      ),
      child: AppText(
        label,
        color: AppColors.green,
        fontSize: 13.sp,
        fontWeight: FontWeight.w700,
      ),
    );
  }
}
