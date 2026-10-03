part of '../../imports.dart';

class TenantProfileScreen extends StatefulWidget {
  const TenantProfileScreen({super.key, this.user});

  final UserModel? user;

  @override
  State<TenantProfileScreen> createState() => _TenantProfileScreenState();
}

class _TenantProfileScreenState extends State<TenantProfileScreen> {
  late final UserModel _fallbackUser;
  late final AccountCubit _profileCubit;
  bool _ownsProfileCubit = false;

  @override
  void initState() {
    super.initState();
    _fallbackUser = widget.user ?? UserModel.currentUser ?? UserModel.initial();
    final AccountCubit? sharedAccount = context.read<AccountCubit?>();
    _ownsProfileCubit = sharedAccount == null;
    _profileCubit = sharedAccount ?? AccountCubit();
    if (_ownsProfileCubit) _profileCubit.restoreCachedProfile();
    if (!_profileCubit.state.isSuccess) {
      _profileCubit.getAccount();
    }
  }

  @override
  void dispose() {
    if (_ownsProfileCubit) _profileCubit.close();
    super.dispose();
  }

  Future<void> _openEditProfile(AccountContent profile) async {
    final UserModel? updated = await Go.to<UserModel>(
      ProfileEditScreen(
        initialValue: profile.accountDetails.editableUser(
          fallback: _fallbackUser,
          fullName: profile.user.fullName,
        ),
        workspace: AppWorkspace.tenant,
      ),
    );
    if (updated != null && mounted) {
      _profileCubit.updateFromUser(updated);
    }
  }

  void _openSummary() => Go.to(const TenantAccountSummaryScreen());

  @override
  Widget build(BuildContext context) {
    // LocaleKeys getters resolve strings without subscribing this screen.
    Localizations.localeOf(context);
    return BlocProvider<AccountCubit>.value(
      value: _profileCubit,
      child: AppScaffold(
        title: LocaleKeys.profileMyAccount,
        showBackButton: false,
        actions: [
          BlocSelector<AccountCubit, AsyncState<AccountContent>, bool>(
            selector: (state) => state.isSuccess,
            builder: (context, isSuccess) => IconButton(
              onPressed: isSuccess ? _openSummary : null,
              style: IconButton.styleFrom(
                backgroundColor: AppColors.white,
                side: const BorderSide(color: AppColors.sokoonBorder),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12.r),
                ),
              ),
              icon: Icon(
                Icons.settings_outlined,
                color: AppColors.sokoonNavy,
                size: 18.r,
              ),
            ),
          ),
        ],
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: StatusBuilder<AccountCubit, AccountContent>.withShimmer(
            initialDataForShimmer: const AccountContent.initial(),
            onRetry: _profileCubit.getAccount,
            errorType: ErrorType.defaultView,
            builder: (profile) => TenantProfileContentView(
              profile: profile,
              onEditPressed: () => _openEditProfile(profile),
            ),
          ).withPullRefresher(onRefresh: _profileCubit.getAccount),
        ),
      ),
    );
  }
}
