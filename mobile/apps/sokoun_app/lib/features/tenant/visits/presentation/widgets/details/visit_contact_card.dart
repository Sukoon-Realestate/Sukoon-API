part of '../../../imports.dart';

class VisitContactCard extends StatelessWidget {
  const VisitContactCard({super.key, required this.ownerPhone});

  final String ownerPhone;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 10.h,
        children: [
          AppText(
            LocaleKeys.tenantVisitContactInfo,
            style: AppTextStyles.bold14.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 11.h),
            decoration: BoxDecoration(
              color: context.appColor(AppColors.greenPale, surface: true),
              borderRadius: BorderRadius.circular(14.r),
            ),
            child: Row(
              spacing: 9.w,
              children: [
                Icon(
                  Icons.phone_outlined,
                  color: context.appColor(AppColors.greenStrong),
                  size: 16.r,
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    spacing: 3.h,
                    children: [
                      AppText(
                        LocaleKeys.tenantVisitOwnerPhoneConfirmed,
                        style: AppTextStyles.extraBold.copyWith(
                          color: context.appColor(AppColors.greenStrong),
                          fontSize: 12.sp,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      AppText(
                        ownerPhone,
                        style: AppTextStyles.bold15.copyWith(
                          color: context.appColor(AppColors.greenStrong),
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
