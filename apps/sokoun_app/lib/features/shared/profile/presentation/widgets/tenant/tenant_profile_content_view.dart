part of '../../../imports.dart';

class TenantProfileContentView extends StatelessWidget {
  const TenantProfileContentView({
    super.key,
    required this.profile,
    required this.onEditPressed,
  });

  final AccountContent profile;
  final VoidCallback onEditPressed;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 24.h),
      children: [
        TenantProfileHeaderCard(profile: profile, onEditPressed: onEditPressed),
        14.szH,
        TenantProfileActions(menuItems: profile.menuItems),
        14.szH,
        ProfileAccountDetailsCard(details: profile.accountDetails),
        14.szH,
        const ProfileLogoutButton(),
        10.szH,
        const ProfileDeleteAccountButton(),
      ],
    );
  }
}
