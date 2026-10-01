part of '../../imports.dart';

class OwnerMoreScreen extends StatefulWidget {
  const OwnerMoreScreen({super.key, this.user});

  final UserModel? user;

  @override
  State<OwnerMoreScreen> createState() => _OwnerMoreScreenState();
}

class _OwnerMoreScreenState extends State<OwnerMoreScreen> {
  late final ValueNotifier<UserModel> _user;
  StreamSubscription<UserState>? _accountSubscription;

  @override
  void initState() {
    super.initState();
    _user = ValueNotifier<UserModel>(
      widget.user ?? UserModel.currentUser ?? UserModel.initial(),
    );
    if (injector.isRegistered<UserCubit>()) {
      _accountSubscription = UserCubit.instance.stream.listen((state) {
        if (state.userStatus == UserStatus.loggedIn) {
          _user.value = state.userModel;
        }
      });
    }
  }

  @override
  void dispose() {
    unawaited(_accountSubscription?.cancel());
    _user.dispose();
    super.dispose();
  }

  Future<void> _openProfile() async {
    await Go.to(OwnerProfileScreen(user: _user.value));
    if (!mounted) {
      return;
    }
    _user.value = UserModel.currentUser ?? _user.value;
  }

  @override
  Widget build(BuildContext context) {
    // LocaleKeys getters resolve strings without subscribing this screen.
    Localizations.localeOf(context);
    return AppScaffold(
      showBackButton: false,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: ListView(
          padding: EdgeInsets.fromLTRB(20.w, 16.h, 20.w, 24.h),
          children: [
            ValueListenableBuilder<UserModel>(
              valueListenable: _user,
              builder: (context, user, _) {
                final String userName = user.name.trim().isEmpty
                    ? LocaleKeys.profileFallbackName
                    : user.name;
                return InkWell(
                  onTap: _openProfile,
                  borderRadius: BorderRadius.circular(16.r),
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 2.h),
                    child: Row(
                      spacing: 12.w,
                      children: [
                        ProfileAvatar(
                          name: userName,
                          accentColor: AppColors.sokoonGold,
                          backgroundColor: AppColors.goldPale,
                          size: 52,
                        ),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            spacing: 3.h,
                            children: [
                              Row(
                                children: [
                                  Flexible(
                                    child: AppText(
                                      userName,
                                      style: AppTextStyles.bold16.copyWith(
                                        color: AppColors.sokoonNavy,
                                        fontSize: 16.sp,
                                        height: 1.45,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              ),
                              AppText(
                                LocaleKeys.profileViewPersonalProfile,
                                style: AppTextStyles.regular12.copyWith(
                                  color: AppColors.sokoonGray,
                                  fontSize: 12.sp,
                                  height: 1.45,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
            22.szH,
            OwnerMoreSection(
              title: LocaleKeys.profileAccountAndProfile,
              items: [
                OwnerMoreItem(
                  icon: Icons.settings_outlined,
                  label: LocaleKeys.profileSettingsTitle,
                  color: AppColors.sokoonTeal,
                  backgroundColor: AppColors.mintLight,
                  onTap: () => Go.to(const ProfileSettingsScreen()),
                ),
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
                  onTap: () => Go.to(const KycIntroScreen()),
                ),
                OwnerMoreItem(
                  icon: Icons.language_rounded,
                  label: LocaleKeys.changeLanguage,
                  color: AppColors.sokoonTeal,
                  backgroundColor: AppColors.mintLight,
                  onTap: () => Go.to(const LanguageSelectionScreen()),
                ),
              ],
            ),
            18.szH,
            OwnerMoreSection(
              title: LocaleKeys.profilePropertyManagement,
              items: [
                OwnerMoreItem(
                  icon: Icons.bar_chart_rounded,
                  label: LocaleKeys.profileAnalyticsStatistics,
                  color: AppColors.blue,
                  backgroundColor: AppColors.bluePale,
                ),
                // OwnerMoreItem(
                //   icon: Icons.calendar_month_outlined,
                //   label: LocaleKeys.profileVisitSchedule,
                //   color: AppColors.sokoonTeal,
                //   backgroundColor: AppColors.mintLight,
                //   onTap: () => Go.to(const OwnerRequestsCalendarScreen()),
                // ),
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
              ],
            ),
            const PublicPageMenu(),
            18.szH,
            const ProfileLogoutButton(),
          ],
        ),
      ),
    );
  }
}
