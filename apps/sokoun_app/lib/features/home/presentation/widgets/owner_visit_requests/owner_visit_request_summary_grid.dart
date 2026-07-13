import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_visit_request_content.dart';

class OwnerVisitRequestSummaryGrid extends StatelessWidget {
  const OwnerVisitRequestSummaryGrid({super.key, required this.summaries});

  final List<OwnerVisitRequestSummaryContent> summaries;

  @override
  Widget build(BuildContext context) {
    return Row(
      textDirection: TextDirection.ltr,
      children: [
        for (int index = 0; index < summaries.length; index++) ...[
          Expanded(child: _SummaryCard(summary: summaries[index])),
          if (index < summaries.length - 1) 8.szW,
        ],
      ],
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.summary});

  final OwnerVisitRequestSummaryContent summary;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 11.h),
      decoration: BoxDecoration(
        color: summary.backgroundColor,
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: summary.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(
            summary.label,
            color: AppColors.sokoonGray,
            fontSize: 11.sp,
            fontWeight: FontWeight.w400,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          4.szH,
          AppText(
            summary.value,
            color: summary.valueColor,
            fontSize: 20.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    );
  }
}
