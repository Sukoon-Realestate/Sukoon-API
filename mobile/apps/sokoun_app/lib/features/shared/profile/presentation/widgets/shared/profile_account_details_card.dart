part of '../../../imports.dart';

class ProfileAccountDetailsCard extends StatelessWidget {
  const ProfileAccountDetailsCard({super.key, required this.details});

  final ProfileAccountDetailsContent details;

  @override
  Widget build(BuildContext context) {
    final String fallback = LocaleKeys.notSetYet;
    final List<({String label, String value, TextDirection? direction})> rows =
        [
          (
            label: LocaleKeys.name,
            value: details.name.trim().isEmpty ? fallback : details.name,
            direction: null,
          ),
          (
            label: LocaleKeys.email,
            value: details.email.trim().isEmpty ? fallback : details.email,
            direction: details.email.trim().isEmpty ? null : TextDirection.ltr,
          ),
          if (details.phoneNumber.isNotEmpty ||
              details.maskedPhoneNumber.isNotEmpty)
            (
              label: LocaleKeys.profileMobile,
              value: details.displayPhone.isEmpty
                  ? fallback
                  : details.displayPhone,
              direction: TextDirection.ltr,
            ),
        ];

    return ProfileSurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(
            LocaleKeys.profileAccountData,
            style: AppTextStyles.bold14.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
          6.szH,
          ...rows.indexed.map((entry) {
            final int index = entry.$1;
            final row = entry.$2;
            return Container(
              padding: EdgeInsets.symmetric(vertical: 10.h),
              decoration: BoxDecoration(
                border: index < rows.length - 1
                    ? Border(
                        bottom: BorderSide(
                          color: context.appColor(AppColors.sokoonBorder),
                        ),
                      )
                    : null,
              ),
              child: ProfileAccountDetailRow(
                label: row.label,
                value: row.value,
                valueDirection: row.direction,
              ),
            );
          }),
        ],
      ),
    );
  }
}
