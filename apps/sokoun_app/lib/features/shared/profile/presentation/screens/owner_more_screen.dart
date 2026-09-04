part of '../../imports.dart';

class OwnerMoreScreen extends StatefulWidget {
  const OwnerMoreScreen({super.key, this.user});

  final UserModel? user;

  @override
  State<OwnerMoreScreen> createState() => _OwnerMoreScreenState();
}

class _OwnerMoreScreenState extends State<OwnerMoreScreen> {
  late UserModel _user;

  @override
  void initState() {
    super.initState();
    _user = widget.user ?? UserModel.currentUser ?? UserModel.initial();
  }

  Future<void> _openProfile() async {
    await Go.to(OwnerProfileScreen(user: _user));
    if (!mounted) {
      return;
    }
    setState(() {
      _user = UserModel.currentUser ?? _user;
    });
  }

  @override
  Widget build(BuildContext context) {
    final String userName = _user.name.trim().isEmpty
        ? LocaleKeys.profileFallbackName
        : _user.name;

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        key: const ValueKey('O-MORE-01'),
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: ListView(
            padding: EdgeInsets.fromLTRB(20.w, 16.h, 20.w, 24.h),
            children: [
              InkWell(
                key: const ValueKey('owner-more-profile-header'),
                onTap: _openProfile,
                borderRadius: BorderRadius.circular(16.r),
                child: Padding(
                  padding: EdgeInsets.symmetric(vertical: 2.h),
                  child: Row(
                    children: [
                      ProfileAvatar(
                        name: userName,
                        accentColor: AppColors.sokoonGold,
                        backgroundColor: AppColors.goldPale,
                        size: 52,
                      ),
                      12.szW,
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Flexible(
                                  child: AppText(
                                    userName,
                                    color: AppColors.sokoonNavy,
                                    fontSize: 16.sp,
                                    fontWeight: FontWeight.w900,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                7.szW,
                                ProfileVerifiedBadge(
                                  text: LocaleKeys.profileVerifiedOwner,
                                ),
                              ],
                            ),
                            3.szH,
                            AppText(
                              LocaleKeys.profileViewPersonalProfile,
                              color: AppColors.sokoonGray,
                              fontSize: 12.sp,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              22.szH,
              OwnerMoreSection(
                title: LocaleKeys.profileAccountAndProfile,
                items: [
                  OwnerMoreItem(
                    icon: Icons.person_outline_rounded,
                    label: LocaleKeys.profileMyProfile,
                    color: AppColors.sokoonTeal,
                    backgroundColor: AppColors.mintLight,
                    onTap: _openProfile,
                  ),
                  OwnerMoreItem(
                    icon: Icons.shield_outlined,
                    label: LocaleKeys.profileVerificationDocuments,
                    color: AppColors.green,
                    backgroundColor: AppColors.greenPale,
                  ),
                  OwnerMoreItem(
                    icon: Icons.lock_outline_rounded,
                    label: LocaleKeys.profilePrivacySecurity,
                    color: AppColors.blue,
                    backgroundColor: AppColors.bluePale,
                  ),
                ],
              ),
              18.szH,
              OwnerMoreSection(
                title: LocaleKeys.profilePropertyManagement,
                items: [
                  OwnerMoreItem(
                    icon: Icons.apartment_rounded,
                    label: LocaleKeys.ownerPropertiesTitle,
                    color: AppColors.sokoonGold,
                    backgroundColor: AppColors.goldPale,
                    onTap: () => Go.to(const OwnerPropertiesScreen()),
                  ),
                  OwnerMoreItem(
                    icon: Icons.bar_chart_rounded,
                    label: LocaleKeys.profileAnalyticsStatistics,
                    color: AppColors.blue,
                    backgroundColor: AppColors.bluePale,
                  ),
                  OwnerMoreItem(
                    icon: Icons.calendar_month_outlined,
                    label: LocaleKeys.profileVisitSchedule,
                    color: AppColors.sokoonTeal,
                    backgroundColor: AppColors.mintLight,
                    onTap: () => Go.to(const OwnerRequestsCalendarScreen()),
                  ),
                ],
              ),
              18.szH,
              OwnerMoreSection(
                title: LocaleKeys.profileSupport,
                items: [
                  OwnerMoreItem(
                    icon: Icons.info_outline_rounded,
                    label: LocaleKeys.profileHelpCenter,
                    color: AppColors.sokoonGray,
                    backgroundColor: AppColors.grayBackground,
                  ),
                  OwnerMoreItem(
                    icon: Icons.description_outlined,
                    label: LocaleKeys.profileTermsPolicies,
                    color: AppColors.sokoonGray,
                    backgroundColor: AppColors.grayBackground,
                  ),
                ],
              ),
              18.szH,
              const ProfileLogoutButton(),
            ],
          ),
        ),
      ),
    );
  }
}
