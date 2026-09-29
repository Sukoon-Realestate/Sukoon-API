part of '../../imports.dart';

class TenantProfileScreen extends StatefulWidget {
  const TenantProfileScreen({super.key, this.user});

  final UserModel? user;

  @override
  State<TenantProfileScreen> createState() => _TenantProfileScreenState();
}

class _TenantProfileScreenState extends State<TenantProfileScreen> {
  late final UserModel _fallbackUser;
  late final TenantProfileCubit _profileCubit;
  late final Future<void> _profileRequest;
  bool _ownsProfileCubit = false;
  StreamSubscription<UserState>? _accountSubscription;

  @override
  void initState() {
    super.initState();
    _fallbackUser = widget.user ?? UserModel.currentUser ?? UserModel.initial();
    try {
      _profileCubit = context.read<TenantProfileCubit>();
    } on ProviderNotFoundException {
      _ownsProfileCubit = true;
      _profileCubit = TenantProfileCubit();
    }
    _profileRequest = _profileCubit.state.isSuccess
        ? Future<void>.value()
        : _profileCubit.getProfile();
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
    if (_ownsProfileCubit) unawaited(_profileCubit.close());
    super.dispose();
  }

  UserModel _editableUser(TenantProfileContent profile) {
    return UserModel(
      id: _fallbackUser.id,
      name: profile.user.fullName.isNotEmpty
          ? profile.user.fullName
          : _fallbackUser.name,
      phone: profile.accountDetails.phoneNumber.isNotEmpty
          ? profile.accountDetails.phoneNumber
          : _fallbackUser.phone,
      email: profile.accountDetails.email.isNotEmpty
          ? profile.accountDetails.email
          : _fallbackUser.email,
      type: _fallbackUser.type,
    );
  }

  Future<void> _openEditProfile(TenantProfileContent profile) async {
    final UserModel? updated = await Go.to<UserModel>(
      TenantEditProfileScreen(initialValue: _editableUser(profile)),
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
    return BlocProvider<TenantProfileCubit>.value(
      value: _profileCubit,
      child: BlocBuilder<TenantProfileCubit, AsyncState<TenantProfileContent>>(
        builder: (context, state) {
          return AppScaffold(
            showBackButton: false,
            backgroundColor: AppColors.scaffoldBackground,
            body: SafeArea(
              child: Column(
                children: [
                  ProfileScreenHeader(
                    title: LocaleKeys.profileMyAccount,
                    trailing: IconButton(
                      onPressed: state.isSuccess ? _openSummary : null,
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
                  Expanded(
                    child:
                        StatusBuilder<
                          TenantProfileCubit,
                          TenantProfileContent
                        >.withShimmer(
                          initialDataForShimmer:
                              const TenantProfileContent.initial(),
                          requestToTryAgainWhenError: _profileRequest,
                          onRetry: _profileCubit.getProfile,
                          errorType: ErrorType.defaultView,
                          builder: (profile) => TenantProfileContentView(
                            profile: profile,
                            onEditPressed: () => _openEditProfile(profile),
                          ),
                        ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
