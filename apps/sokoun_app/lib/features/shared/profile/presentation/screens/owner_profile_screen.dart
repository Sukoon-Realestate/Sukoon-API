part of '../../imports.dart';

class OwnerProfileScreen extends StatefulWidget {
  const OwnerProfileScreen({super.key, required this.user});

  final UserModel user;

  @override
  State<OwnerProfileScreen> createState() => _OwnerProfileScreenState();
}

class _OwnerProfileScreenState extends State<OwnerProfileScreen> {
  late final OwnerProfileCubit _profileCubit;
  StreamSubscription<UserState>? _accountSubscription;

  @override
  void initState() {
    super.initState();
    _profileCubit = OwnerProfileCubit();
    _profileCubit.getProfile();
    if (injector.isRegistered<UserCubit>()) {
      _accountSubscription = UserCubit.instance.stream.listen((state) {
        if (state.userStatus == UserStatus.loggedIn) {
          _profileCubit.updateFromUser(state.userModel);
          unawaited(_profileCubit.getProfile());
        }
      });
    }
  }

  @override
  void dispose() {
    unawaited(_accountSubscription?.cancel());
    _profileCubit.close();
    super.dispose();
  }

  Future<void> _openEditProfile(OwnerProfileContent profile) async {
    final UserModel? updated = await Go.to<UserModel>(
      ProfileEditScreen(
        initialValue: profile.accountDetails.editableUser(
          fallback: widget.user,
          fullName: profile.owner.fullName,
        ),
        workspace: AppWorkspace.owner,
      ),
    );
    if (updated != null && mounted) {
      _profileCubit.updateFromUser(updated);
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<OwnerProfileCubit>.value(
      value: _profileCubit,
      child: AppScaffold(
        title: LocaleKeys.profileOwnerTitle,
        showBackButton: true,
        actions: [
          BlocSelector<
            OwnerProfileCubit,
            AsyncState<OwnerProfileContent>,
            bool
          >(
            selector: (state) => state.isSuccess,
            builder: (context, isSuccess) => IconButton(
              onPressed: isSuccess
                  ? () => _openEditProfile(_profileCubit.data)
                  : null,
              icon: Icon(
                Icons.edit_outlined,
                color: AppColors.sokoonNavy,
                size: 18.r,
              ),
            ),
          ),
        ],
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child:
              StatusBuilder<OwnerProfileCubit, OwnerProfileContent>.withShimmer(
                initialDataForShimmer: const OwnerProfileContent.initial(),
                onRetry: _profileCubit.getProfile,
                errorType: ErrorType.defaultView,
                builder: (profile) => OwnerProfileContentView(profile: profile),
              ).withPullRefresher(onRefresh: _profileCubit.getProfile),
        ),
      ),
    );
  }
}
