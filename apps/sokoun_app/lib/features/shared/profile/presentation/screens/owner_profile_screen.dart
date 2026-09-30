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

  UserModel _editableUser(OwnerProfileContent profile) {
    return UserModel(
      id: widget.user.id,
      name: profile.owner.fullName.isNotEmpty
          ? profile.owner.fullName
          : widget.user.name,
      phone: profile.accountDetails.phoneNumber.isNotEmpty
          ? profile.accountDetails.phoneNumber
          : widget.user.phone,
      email: profile.accountDetails.email.isNotEmpty
          ? profile.accountDetails.email
          : widget.user.email,
      type: widget.user.type,
    );
  }

  Future<void> _openEditProfile(OwnerProfileContent profile) async {
    final UserModel? updated = await Go.to<UserModel>(
      OwnerEditProfileScreen(initialValue: _editableUser(profile)),
    );
    if (updated != null && mounted) {
      _profileCubit.updateFromUser(updated);
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<OwnerProfileCubit>.value(
      value: _profileCubit,
      child: BlocBuilder<OwnerProfileCubit, AsyncState<OwnerProfileContent>>(
        builder: (context, state) {
          return AppScaffold(
            title: LocaleKeys.profileOwnerTitle,
            showBackButton: true,
            actions: [
              IconButton(
                onPressed: state.isSuccess
                    ? () => _openEditProfile(state.data)
                    : null,
                icon: Icon(
                  Icons.edit_outlined,
                  color: AppColors.sokoonNavy,
                  size: 18.r,
                ),
              ),
            ],
            backgroundColor: AppColors.scaffoldBackground,
            body: SafeArea(
              child:
                  StatusBuilder<
                        OwnerProfileCubit,
                        OwnerProfileContent
                      >.withShimmer(
                        initialDataForShimmer:
                            const OwnerProfileContent.initial(),
                        onRetry: _profileCubit.getProfile,
                        errorType: ErrorType.defaultView,
                        builder: (profile) =>
                            OwnerProfileContentView(profile: profile),
                      )
                      .withPullRefresher(onRefresh: _profileCubit.getProfile),
            ),
          );
        },
      ),
    );
  }
}
