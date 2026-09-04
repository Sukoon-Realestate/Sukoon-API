part of '../../imports.dart';

class OwnerProfileScreen extends StatefulWidget {
  const OwnerProfileScreen({super.key, required this.user});

  final UserModel user;

  @override
  State<OwnerProfileScreen> createState() => _OwnerProfileScreenState();
}

class _OwnerProfileScreenState extends State<OwnerProfileScreen> {
  late UserModel _user;

  @override
  void initState() {
    super.initState();
    _user = widget.user;
  }

  Future<void> _openEditProfile() async {
    final UserModel? updated = await Go.to<UserModel>(
      OwnerEditProfileScreen(initialValue: _user),
    );
    if (updated != null && mounted) {
      setState(() => _user = updated);
    }
  }

  @override
  Widget build(BuildContext context) {
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
                  onPressed: _openEditProfile,
                  icon: Icon(
                    Icons.edit_outlined,
                    color: AppColors.sokoonNavy,
                    size: 18.r,
                  ),
                ),
              ),
              Expanded(
                child: ListView(
                  padding: EdgeInsets.fromLTRB(20.w, 14.h, 20.w, 24.h),
                  children: [
                    OwnerProfileHeaderCard(user: _user),
                    14.szH,
                    ProfileAccountDetailsCard(user: _user),
                    14.szH,
                    ProfileVerificationBanner(
                      title: '',
                      description: LocaleKeys.profileOwnerPhonePrivacy,
                      isPrivacy: true,
                    ),
                    14.szH,
                    const OwnerReviewsCard(),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
