part of '../../imports.dart';

class TenantProfileScreen extends StatefulWidget {
  const TenantProfileScreen({super.key, this.user});

  final UserModel? user;

  @override
  State<TenantProfileScreen> createState() => _TenantProfileScreenState();
}

class _TenantProfileScreenState extends State<TenantProfileScreen> {
  late UserModel _user;

  @override
  void initState() {
    super.initState();
    _user = widget.user ?? UserModel.currentUser ?? UserModel.initial();
  }

  Future<void> _openEditProfile() async {
    final UserModel? updated = await Go.to<UserModel>(
      TenantEditProfileScreen(initialValue: _user),
    );
    if (updated != null && mounted) {
      setState(() => _user = updated);
    }
  }

  void _openSummary() {
    Go.to(TenantAccountSummaryScreen(user: _user));
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        key: const ValueKey('T-PROFILE-01'),
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              ProfileScreenHeader(
                title: LocaleKeys.profileMyAccount,
                trailing: IconButton(
                  key: const ValueKey('tenant-profile-summary'),
                  onPressed: _openSummary,
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
                child: ListView(
                  padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 24.h),
                  children: [
                    TenantProfileHeaderCard(
                      user: _user,
                      onEditPressed: _openEditProfile,
                    ),
                    14.szH,
                    const TenantProfileActions(),
                    14.szH,
                    ProfileAccountDetailsCard(user: _user),
                    14.szH,
                    const ProfileLogoutButton(),
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
