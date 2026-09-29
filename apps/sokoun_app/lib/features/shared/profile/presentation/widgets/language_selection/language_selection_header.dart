part of '../../../imports.dart';

class LanguageSelectionHeader extends StatelessWidget {
  const LanguageSelectionHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 60.r,
          height: 60.r,
          decoration: BoxDecoration(
            color: AppColors.sokoonTeal,
            borderRadius: BorderRadius.circular(13.r),
            boxShadow: [
              BoxShadow(
                color: AppColors.tealAlpha19,
                blurRadius: 16.r,
                offset: Offset(0, 6.h),
              ),
            ],
          ),
          child: Icon(
            Icons.translate_rounded,
            color: AppColors.white,
            size: 36.r,
          ),
        ),
        24.szH,
        AppText(
          LocaleKeys.languageSelectionTitle,
          style: AppTextStyles.bold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 22.sp,
            height: 1.5,
          ),
          textAlign: TextAlign.center,
        ),
        8.szH,
        AppText(
          LocaleKeys.languageSelectionSubtitle,
          style: AppTextStyles.regular14.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 14.sp,
            height: 1.5,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
