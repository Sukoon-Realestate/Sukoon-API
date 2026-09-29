part of '../../../imports.dart';

class ProfileAccountDetailsCard extends StatelessWidget {
  const ProfileAccountDetailsCard({super.key, required this.details});

  final ProfileAccountDetailsContent details;

  @override
  Widget build(BuildContext context) {
    final String fallback = LocaleKeys.notSetYet;
    final List<({String label, String value})> rows = [
      (
        label: LocaleKeys.name,
        value: details.name.trim().isEmpty ? fallback : details.name,
      ),
      (
        label: LocaleKeys.email,
        value: details.email.trim().isEmpty ? fallback : details.email,
      ),
      if (details.phoneNumber.isNotEmpty ||
          details.maskedPhoneNumber.isNotEmpty)
        (
          label: LocaleKeys.profileMobile,
          value: details.displayPhone.isEmpty ? fallback : details.displayPhone,
        ),
    ];

    return ProfileSurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(
            LocaleKeys.profileAccountData,
            style: AppTextStyles.bold14.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
          6.szH,
          ...rows.indexed.map((entry) {
            final int index = entry.$1;
            final ({String label, String value}) row = entry.$2;
            return Container(
              padding: EdgeInsets.symmetric(vertical: 10.h),
              decoration: BoxDecoration(
                border: index < rows.length - 1
                    ? const Border(
                        bottom: BorderSide(color: AppColors.sokoonBorder),
                      )
                    : null,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: AppText(
                      row.value,
                      style: AppTextStyles.bold14.copyWith(
                        color: AppColors.sokoonNavy,
                        fontSize: 14.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  12.szW,
                  AppText(
                    row.label,
                    style: AppTextStyles.regular12.copyWith(
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      height: 1.45,
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
