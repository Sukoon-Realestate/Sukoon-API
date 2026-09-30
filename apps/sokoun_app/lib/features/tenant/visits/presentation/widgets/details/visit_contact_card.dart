part of '../../../imports.dart';

class VisitContactCard extends StatelessWidget {
  const VisitContactCard({super.key, required this.ownerPhone});

  final String ownerPhone;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 10.h,
        children: [
          AppText(
            LocaleKeys.tenantVisitContactInfo,
            style: AppTextStyles.bold14.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 11.h),
            decoration: BoxDecoration(
              color: AppColors.greenPale,
              borderRadius: BorderRadius.circular(14.r),
            ),
            child: Row(
              spacing: 9.w,
              children: [
                Icon(Icons.phone_outlined, color: AppColors.green, size: 16.r),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    spacing: 3.h,
                    children: [
                      AppText(
                        LocaleKeys.tenantVisitOwnerPhoneConfirmed,
                        style: AppTextStyles.extraBold.copyWith(
                          color: AppColors.green,
                          fontSize: 11.sp,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      AppText(
                        ownerPhone,
                        style: AppTextStyles.bold15.copyWith(
                          color: AppColors.green,
                          fontSize: 15.sp,
                          height: 1.45,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
