part of '../../imports.dart';

class TenantProfileScreen extends StatefulWidget {
  const TenantProfileScreen({
    super.key,
    this.user,
    this.showBackButton = false,
  });

  final UserModel? user;
  final bool showBackButton;

  @override
  State<TenantProfileScreen> createState() => _TenantProfileScreenState();
}

class _TenantProfileScreenState extends State<TenantProfileScreen> {
  late final UserModel _fallbackUser;
  late final AccountCubit _profileCubit;
  late Future<void> _profileRequest;
  bool _ownsProfileCubit = false;

  @override
  void initState() {
    super.initState();
    _fallbackUser = widget.user ?? UserModel.currentUser ?? UserModel.initial();
    final AccountCubit? sharedAccount = context.read<AccountCubit?>();
    _ownsProfileCubit = sharedAccount == null;
    _profileCubit = sharedAccount ?? AccountCubit();
    if (_ownsProfileCubit) _profileCubit.restoreCachedProfile();
    _profileRequest = _profileCubit.state.isSuccess
        ? Future<void>.value()
        : _profileCubit.getAccount();
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

  Future<void> _refreshProfile() {
    if (_profileCubit.isLoading) return _profileRequest;
    return _profileRequest = _profileCubit.getAccount();
  }

  @override
  Widget build(BuildContext context) {
    Localizations.localeOf(context);
    return BlocProvider<AccountCubit>.value(
      value: _profileCubit,
      child: ProfileScaffold(
        workspace: AppWorkspace.tenant,
        showBackButton: widget.showBackButton,
        body: StatusBuilder<AccountCubit, AccountContent>.withShimmer(
          initialDataForShimmer: const AccountContent.initial(),
          onRetry: _refreshProfile,
          errorType: ErrorType.defaultView,
          builder: (profile) => TenantProfileContentView(
            profile: profile,
            onEditPressed: () => _openEditProfile(profile),
          ),
        ).withPullRefresher(onRefresh: _refreshProfile),
      ),
    );
  }
}
