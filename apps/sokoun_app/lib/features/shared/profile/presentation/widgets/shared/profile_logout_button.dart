part of '../../../imports.dart';

class ProfileLogoutButton extends StatelessWidget {
  const ProfileLogoutButton({super.key});

  Future<void> _logout() async {
    await NotificationDeviceData.unregisterCurrentDevice();
    await UserCubit.instance.logout();
  }

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: LocaleKeys.profileLogout,
      child: InkWell(
        onTap: _logout,
        borderRadius: BorderRadius.circular(16.r),
        child: Container(
          width: double.infinity,
          padding: EdgeInsets.symmetric(vertical: 15.h),
          decoration: BoxDecoration(
            color: AppColors.redPale,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(color: AppColors.red.withValues(alpha: .18)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.logout_rounded, color: AppColors.red, size: 18.r),
              8.szW,
              AppText(
                LocaleKeys.profileLogout,
                color: AppColors.red,
                fontSize: 14.sp,
                fontWeight: FontWeight.w700,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
