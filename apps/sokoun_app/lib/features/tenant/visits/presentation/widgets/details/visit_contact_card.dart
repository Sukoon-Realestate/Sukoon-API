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
        children: [
          AppText(
            LocaleKeys.tenantVisitContactInfo,
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
          10.szH,
          Container(
            padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 11.h),
            decoration: BoxDecoration(
              color: AppColors.greenPale,
              borderRadius: BorderRadius.circular(14.r),
            ),
            child: Row(
              children: [
                Icon(Icons.phone_outlined, color: AppColors.green, size: 16.r),
                9.szW,
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      AppText(
                        LocaleKeys.tenantVisitOwnerPhoneConfirmed,
                        color: AppColors.green,
                        fontSize: 11.sp,
                        fontWeight: FontWeight.w800,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      3.szH,
                      AppText(
                        ownerPhone,
                        color: AppColors.green,
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w900,
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
