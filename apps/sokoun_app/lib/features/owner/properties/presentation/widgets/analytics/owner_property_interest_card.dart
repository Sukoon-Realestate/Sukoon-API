part of '../../../imports.dart';

class OwnerPropertyInterestCard extends StatelessWidget {
  const OwnerPropertyInterestCard({super.key, required this.items});

  final List<OwnerPropertyInterestItem> items;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            LocaleKeys.ownerAnalyticsTopInterests,
            color: AppColors.sokoonNavy,
            fontSize: 15.sp,
            fontWeight: FontWeight.w700,
          ),
          16.szH,
          for (int index = 0; index < items.length; index++) ...[
            _InterestProgress(item: items[index]),
            if (index < items.length - 1) 14.szH,
          ],
        ],
      ),
    );
  }
}

class OwnerPropertyInterestItem {
  const OwnerPropertyInterestItem({required this.label, required this.value});

  final String label;
  final int value;
}

class _InterestProgress extends StatelessWidget {
  const _InterestProgress({required this.item});

  final OwnerPropertyInterestItem item;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            AppText(
              item.label,
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              fontWeight: FontWeight.w700,
            ),
            const Spacer(),
            AppText(
              '${item.value}%',
              color: AppColors.sokoonNavy,
              fontSize: 13.sp,
              fontWeight: FontWeight.w700,
            ),
          ],
        ),
        7.szH,
        ClipRRect(
          borderRadius: BorderRadius.circular(99.r),
          child: LinearProgressIndicator(
            value: item.value / 100,
            minHeight: 7.h,
            backgroundColor: AppColors.grayBackground,
            valueColor: const AlwaysStoppedAnimation<Color>(
              AppColors.sokoonTeal,
            ),
          ),
        ),
      ],
    );
  }
}
