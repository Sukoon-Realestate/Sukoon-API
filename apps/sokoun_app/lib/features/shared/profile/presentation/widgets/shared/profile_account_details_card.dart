part of '../../../imports.dart';

class ProfileAccountDetailsCard extends StatelessWidget {
  const ProfileAccountDetailsCard({super.key, required this.user});

  final UserModel user;

  @override
  Widget build(BuildContext context) {
    final String fallback = LocaleKeys.notSetYet;
    final List<({String label, String value})> rows = [
      (
        label: LocaleKeys.name,
        value: user.name.trim().isEmpty ? fallback : user.name,
      ),
      (
        label: LocaleKeys.email,
        value: user.email.trim().isEmpty ? fallback : user.email,
      ),
      (
        label: LocaleKeys.profileMobile,
        value: user.phone.trim().isEmpty ? fallback : _maskedPhone(user.phone),
      ),
    ];

    return ProfileSurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(
            LocaleKeys.profileAccountData,
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
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
                      color: AppColors.sokoonNavy,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w700,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  12.szW,
                  AppText(
                    row.label,
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  String _maskedPhone(String phone) {
    final String normalized = phone.trim();
    if (normalized.length < 7) {
      return normalized;
    }
    return '${normalized.substring(0, 3)}****${normalized.substring(normalized.length - 3)}';
  }
}
