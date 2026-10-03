part of '../../imports.dart';

class ProfileDeleteAccountScreen extends StatefulWidget {
  const ProfileDeleteAccountScreen({super.key});
  @override
  State<ProfileDeleteAccountScreen> createState() =>
      _ProfileDeleteAccountScreenState();
}

class _ProfileDeleteAccountScreenState
    extends State<ProfileDeleteAccountScreen> {
  late final ProfileDeleteAccountCubit _cubit;
  final ValueNotifier<bool> _deleting = ValueNotifier(false);
  final ValueNotifier<bool> _confirmed = ValueNotifier(false);
  @override
  void initState() {
    super.initState();
    _cubit = ProfileDeleteAccountCubit();
  }

  @override
  void dispose() {
    _cubit.close();
    _confirmed.dispose();
    _deleting.dispose();
    super.dispose();
  }

  Future<void> _delete(BuildContext context) async {
    if (!_confirmed.value || _deleting.value) return;
    _deleting.value = true;
    try {
      bool deleted = false;
      await _cubit.deleteAccount(onSuccess: () => deleted = true);
      if (!deleted || !mounted) return;
      await Future.wait([
        NotificationDeviceData.stop(),
        UserCubit.instance.logout(),
      ]);
    } finally {
      if (mounted) _deleting.value = false;
    }
  }

  @override
  Widget build(BuildContext context) => ValueListenableBuilder<bool>(
    valueListenable: _deleting,
    builder: (context, deleting, _) => PopScope(
      canPop: !deleting,
      child: AppScaffold(
        isBackEnabled: !deleting,
        title: LocaleKeys.deleteAccount,
        contentWidth: SokounContentWidth.form,
        body: SafeArea(
          child: ListView(
            padding: EdgeInsets.all(20.r),
            children: [
              const ProfileDeletionContent(),
              24.szH,
              ValueListenableBuilder<bool>(
                valueListenable: _confirmed,
                builder: (context, confirmed, _) => CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  controlAffinity: ListTileControlAffinity.leading,
                  value: confirmed,
                  onChanged: deleting
                      ? null
                      : (value) => _confirmed.value = value ?? false,
                  title: AppText(
                    LocaleKeys.settingsDeleteAcknowledgement,
                    style: AppTextStyles.regular14.copyWith(height: 1.6),
                  ),
                ),
              ),
            ],
          ),
        ),
        bottomBar: SokounActionFooter(
          width: SokounContentWidth.form,
          child: ValueListenableBuilder<bool>(
            valueListenable: _confirmed,
            builder: (context, confirmed, _) => confirmed
                ? AppLoadingButton(
                    asyncCall: _delete,
                    title: LocaleKeys.settingsDeletePermanently,
                    buttonColor: AppColors.sokoonRose,
                  )
                : DefaultButton(
                    title: LocaleKeys.settingsDeletePermanently,
                    disabled: true,
                    color: AppColors.grayPale,
                    textColor: AppColors.sokoonGray,
                  ),
          ),
        ),
      ),
    ),
  );
}
