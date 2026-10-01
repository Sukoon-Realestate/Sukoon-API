part of '../../../imports.dart';

class ProfileLogoutButton extends StatefulWidget {
  const ProfileLogoutButton({super.key});
  @override
  State<ProfileLogoutButton> createState() => _ProfileLogoutButtonState();
}

class _ProfileLogoutButtonState extends State<ProfileLogoutButton> {
  late final ProfileLogoutCubit _cubit;
  @override
  void initState() {
    super.initState();
    _cubit = ProfileLogoutCubit();
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  Future<void> _logout(BuildContext context) async {
    if (_cubit.isLoading) return;
    await NotificationDeviceData.unregisterCurrentDevice();
    if (await _cubit.logout()) await UserCubit.instance.logout();
  }

  @override
  Widget build(BuildContext context) => AppLoadingButton(
    asyncCall: _logout,
    title: LocaleKeys.profileLogout,
    buttonColor: AppColors.redPale,
    textColor: AppColors.red,
    icon: Icon(Icons.logout_rounded, color: AppColors.red, size: 18.r),
    borderRadius: 16.r,
  );
}
