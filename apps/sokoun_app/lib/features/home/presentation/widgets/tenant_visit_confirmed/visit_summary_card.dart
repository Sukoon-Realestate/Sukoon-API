import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class VisitSummaryCard extends StatelessWidget {
  const VisitSummaryCard({super.key, required this.rows});

  final List<VisitSummaryRowData> rows;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
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
          for (int index = 0; index < rows.length; index++) ...[
            _SummaryRow(row: rows[index]),
            if (index < rows.length - 1)
              const Divider(color: AppColors.sokoonBorder),
          ],
        ],
      ),
    );
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow({required this.row});

  final VisitSummaryRowData row;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 38.h,
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Flexible(
            child: AppText(
              row.value,
              color: AppColors.sokoonNavy,
              fontSize: 12.sp,
              fontWeight: FontWeight.w900,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const Spacer(),
          AppText(
            row.label,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w500,
          ),
        ],
      ),
    );
  }
}

class VisitSummaryRowData {
  const VisitSummaryRowData({required this.label, required this.value});

  final String label;
  final String value;
}
