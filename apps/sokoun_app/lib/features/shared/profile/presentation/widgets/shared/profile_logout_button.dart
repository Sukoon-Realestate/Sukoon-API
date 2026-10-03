part of '../../../imports.dart';

class ProfileLogoutButton extends StatefulWidget {
  const ProfileLogoutButton({super.key});
  @override
  State<ProfileLogoutButton> createState() => _ProfileLogoutButtonState();
}

class _ProfileLogoutButtonState extends State<ProfileLogoutButton> {
  late final ProfileLogoutCubit _cubit;
  bool _confirming = false;
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
    if (_cubit.isLoading || _confirming) return;
    _confirming = true;
    final bool? confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
      ),
      builder: (_) => const ProfileLogoutSheet(),
    );
    _confirming = false;
    if (confirmed != true || !mounted) return;
    if (!await _cubit.logout()) return;
    await Future.wait([
      NotificationDeviceData.stop(),
      UserCubit.instance.logout(),
    ]);
  }

  @override
  Widget build(BuildContext context) => UnsavedChangesGuard(
    hasChanges: () => false,
    isSaving: () => _cubit.isLoading,
    child: BlocProvider.value(
      value: _cubit,
      child: BlocBuilder<ProfileLogoutCubit, AsyncState<bool>>(
        builder: (context, state) => DefaultButton(
          onTap: () => _logout(context),
          title: LocaleKeys.profileLogout,
          disabled: state.isLoading,
          color: AppColors.redPale,
          textColor: AppColors.sokoonNavy,
          customChild: state.isLoading
              ? Semantics(
                  label: LocaleKeys.profileLogout,
                  liveRegion: true,
                  child: CustomLoading.showLoadingView(size: 20.r),
                )
              : null,
        ),
      ),
    ),
  );
}
