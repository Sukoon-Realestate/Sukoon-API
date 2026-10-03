part of '../../imports.dart';

class OwnerProfileScreen extends StatefulWidget {
  const OwnerProfileScreen({super.key, this.user, this.showBackButton = false});

  final UserModel? user;
  final bool showBackButton;

  @override
  State<OwnerProfileScreen> createState() => _OwnerProfileScreenState();
}

class _OwnerProfileScreenState extends State<OwnerProfileScreen> {
  late final OwnerProfileCubit _profileCubit;
  late final UserModel _fallbackUser;
  late Future<void> _profileRequest;
  StreamSubscription<UserState>? _accountSubscription;

  @override
  void initState() {
    super.initState();
    _fallbackUser = widget.user ?? UserModel.currentUser ?? UserModel.initial();
    _profileCubit = OwnerProfileCubit();
    _profileRequest = _profileCubit.getProfile();
    if (injector.isRegistered<UserCubit>()) {
      _accountSubscription = UserCubit.instance.stream.listen((state) {
        if (state.userStatus == UserStatus.loggedIn) {
          _profileCubit.updateFromUser(state.userModel);
          _refreshProfile();
        }
      });
    }
  }

  @override
  void dispose() {
    _accountSubscription?.cancel();
    _profileCubit.close();
    super.dispose();
  }

  Future<void> _openEditProfile(OwnerProfileContent profile) async {
    final UserModel? updated = await Go.to<UserModel>(
      ProfileEditScreen(
        initialValue: profile.accountDetails.editableUser(
          fallback: UserModel.currentUser ?? _fallbackUser,
          fullName: profile.owner.fullName,
        ),
        workspace: AppWorkspace.owner,
      ),
    );
    if (updated != null && mounted) {
      _profileCubit.updateFromUser(updated);
    }
  }

  Future<void> _refreshProfile() {
    if (_profileCubit.isLoading) return _profileRequest;
    return _profileRequest = _profileCubit.getProfile();
  }

  @override
  Widget build(BuildContext context) {
    Localizations.localeOf(context);
    return BlocProvider<OwnerProfileCubit>.value(
      value: _profileCubit,
      child: ProfileScaffold(
        workspace: AppWorkspace.owner,
        showBackButton: widget.showBackButton,
        body: StatusBuilder<OwnerProfileCubit, OwnerProfileContent>.withShimmer(
          initialDataForShimmer: const OwnerProfileContent.initial(),
          onRetry: _refreshProfile,
          errorType: ErrorType.defaultView,
          builder: (profile) => OwnerProfileContentView(
            profile: profile,
            onEditPressed: () => _openEditProfile(profile),
          ),
        ).withPullRefresher(onRefresh: _refreshProfile),
      ),
    );
  }
}
