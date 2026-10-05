import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class KycStatusSummaryRow {
  const KycStatusSummaryRow({required this.label, required this.value});

  final String label;
  final String value;
}

class KycStatusSummaryCard extends StatelessWidget {
  const KycStatusSummaryCard({super.key, required this.rows});

  final List<KycStatusSummaryRow> rows;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
        boxShadow: const [
          BoxShadow(
            color: AppColors.shadowBlack04,
            offset: Offset(0, 2),
            blurRadius: 4,
          ),
        ],
      ),
      child: Column(
        children: List.generate(rows.length, (index) {
          final row = rows[index];
          final isLast = index == rows.length - 1;

          return Container(
            padding: EdgeInsets.symmetric(vertical: 10.h),
            decoration: BoxDecoration(
              border: isLast
                  ? null
                  : Border(
                      bottom: BorderSide(
                        color: context.appColor(AppColors.sokoonBorder),
                      ),
                    ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: AppText(
                    row.value,
                    style: AppTextStyles.extraBold13.copyWith(
                      color: context.appColor(AppColors.sokoonNavy),
                      fontSize: 13.sp,
                      height: 1.45,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                AppText(
                  row.label,
                  style: AppTextStyles.regular12.copyWith(
                    color: context.appColor(AppColors.sokoonGray),
                    fontSize: 12.sp,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          );
        }),
      ),
    );
  }
}
