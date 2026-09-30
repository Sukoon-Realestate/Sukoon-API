part of '../../../imports.dart';

class VisitSummaryCard extends StatelessWidget {
  const VisitSummaryCard({super.key, required this.rows});

  final List<({String label, String value})> rows;

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
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          for (int index = 0; index < rows.length; index++) ...[
            _VisitSummaryRow(row: rows[index]),
            if (index < rows.length - 1)
              const Divider(height: 1, color: AppColors.sokoonBorder),
          ],
        ],
      ),
    );
  }
}

class _VisitSummaryRow extends StatelessWidget {
  const _VisitSummaryRow({required this.row});

  final ({String label, String value}) row;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: BoxConstraints(minHeight: 43.h),
      child: Row(
        spacing: 12.w,
        children: [
          Expanded(
            child: AppText(
              row.value,
              style: AppTextStyles.extraBold13.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 13.sp,
                height: 1.45,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          AppText(
            row.label,
            style: AppTextStyles.regular12.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
              height: 1.45,
            ),
            maxLines: 1,
          ),
        ],
      ),
    );
  }
}
