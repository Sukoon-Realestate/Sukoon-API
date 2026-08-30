import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

class OwnerVisitRequestSummaryGrid extends StatelessWidget {
  const OwnerVisitRequestSummaryGrid({
    super.key,
    required this.totalCount,
    required this.pendingCount,
  });

  final int totalCount;
  final int pendingCount;

  @override
  Widget build(BuildContext context) {
    return Row(
      textDirection: TextDirection.rtl,
      children: [
        Expanded(
          child: _SummaryCard(
            label: LocaleKeys.ownerVisitsTotalRequests,
            value: '$totalCount',
            backgroundColor: AppColors.tealAlpha07,
            borderColor: AppColors.tealAlpha19,
            valueColor: AppColors.sokoonTeal,
          ),
        ),
        8.szW,
        Expanded(
          child: _SummaryCard(
            label: LocaleKeys.ownerVisitsWaitingForReply,
            value: '$pendingCount',
            backgroundColor: AppColors.goldAlpha15,
            borderColor: AppColors.goldAlpha15,
            valueColor: AppColors.gold,
          ),
        ),
      ],
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({
    required this.label,
    required this.value,
    required this.backgroundColor,
    required this.borderColor,
    required this.valueColor,
  });

  final String label;
  final String value;
  final Color backgroundColor;
  final Color borderColor;
  final Color valueColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 11.h),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(
            label,
            color: AppColors.sokoonGray,
            fontSize: 11.sp,
            fontWeight: FontWeight.w400,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          4.szH,
          AppText(
            value,
            color: valueColor,
            fontSize: 20.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    );
  }
}
