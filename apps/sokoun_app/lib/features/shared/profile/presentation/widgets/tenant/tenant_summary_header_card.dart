part of '../../../imports.dart';

class TenantSummaryHeaderCard extends StatelessWidget {
  const TenantSummaryHeaderCard({super.key, required this.user});

  final UserModel user;

  @override
  Widget build(BuildContext context) {
    final String userName = user.name.trim().isEmpty
        ? LocaleKeys.profileFallbackName
        : user.name;

    return Container(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 22.h),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
          colors: [AppColors.sokoonTeal, Color(0xFF065F57)],
        ),
        borderRadius: BorderRadius.circular(20.r),
      ),
      child: Column(
        children: [
          Row(
            children: [
              ProfileAvatar(
                name: userName,
                accentColor: AppColors.sokoonTeal,
                backgroundColor: AppColors.whiteAlpha10,
                size: 56,
                useInitial: true,
              ),
              14.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AppText(
                      userName,
                      color: AppColors.white,
                      fontSize: 18.sp,
                      fontWeight: FontWeight.w900,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    3.szH,
                    AppText(
                      LocaleKeys.profileTenantSummaryMemberSince,
                      color: AppColors.whiteAlpha60,
                      fontSize: 12.sp,
                    ),
                  ],
                ),
              ),
            ],
          ),
          16.szH,
          Row(
            children: [
              AppText(
                LocaleKeys.profileCompletion,
                color: AppColors.whiteAlpha60,
                fontSize: 12.sp,
              ),
              const Spacer(),
              AppText(
                '80%',
                color: AppColors.white,
                fontSize: 12.sp,
                fontWeight: FontWeight.w800,
              ),
            ],
          ),
          7.szH,
          ClipRRect(
            borderRadius: BorderRadius.circular(99.r),
            child: LinearProgressIndicator(
              value: .8,
              minHeight: 6.h,
              color: AppColors.white,
              backgroundColor: AppColors.whiteAlpha40,
            ),
          ),
        ],
      ),
    );
  }
}
