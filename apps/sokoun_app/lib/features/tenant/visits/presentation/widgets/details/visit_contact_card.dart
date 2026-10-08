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
          RevealedPhoneCard(phoneNumber: ownerPhone),
        ],
      ),
    );
  }
}
