part of '../../imports.dart';

class OwnerProfileScreen extends StatefulWidget {
  const OwnerProfileScreen({super.key, required this.user});

  final UserModel user;

  @override
  State<OwnerProfileScreen> createState() => _OwnerProfileScreenState();
}

class _OwnerProfileScreenState extends State<OwnerProfileScreen> {
  late final OwnerProfileCubit _profileCubit;
  late final Future<void> _profileRequest;

  @override
  void initState() {
    super.initState();
    _profileCubit = OwnerProfileCubit();
    _profileRequest = _profileCubit.getProfile();
  }

  @override
  void dispose() {
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
      type: UserType.owner.name,
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
          return Directionality(
            textDirection: TextDirection.rtl,
            child: Scaffold(
              key: const ValueKey('O-PROFILE-01'),
              backgroundColor: AppColors.scaffoldBackground,
              body: SafeArea(
                child: Column(
                  children: [
                    ProfileScreenHeader(
                      title: LocaleKeys.profileOwnerTitle,
                      showBackButton: true,
                      trailing: IconButton(
                        key: const ValueKey('owner-profile-edit'),
                        onPressed: state.isSuccess
                            ? () => _openEditProfile(state.data)
                            : null,
                        icon: Icon(
                          Icons.edit_outlined,
                          color: AppColors.sokoonNavy,
                          size: 18.r,
                        ),
                      ),
                    ),
                    Expanded(
                      child:
                          StatusBuilder<
                            OwnerProfileCubit,
                            OwnerProfileContent
                          >.withShimmer(
                            initialDataForShimmer:
                                const OwnerProfileContent.initial(),
                            requestToTryAgainWhenError: _profileRequest,
                            errorType: ErrorType.defaultView,
                            builder: (profile) =>
                                OwnerProfileContentView(profile: profile),
                          ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
