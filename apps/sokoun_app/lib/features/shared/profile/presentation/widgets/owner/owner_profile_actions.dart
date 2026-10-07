part of '../../../imports.dart';

class OwnerProfileActions extends StatelessWidget {
  const OwnerProfileActions({super.key});

  @override
  Widget build(BuildContext context) => Column(
    spacing: 8.h,
    children: [
      ProfileSurfaceCard(
        child: ProfileMenuTile(
          icon: Icons.account_balance_wallet_outlined,
          label: LocaleKeys.ownerRevenueTitle,
          iconColor: context.appColor(AppColors.sokoonTeal),
          iconBackgroundColor: context.appColor(
            AppColors.mintLight,
            surface: true,
          ),
          onTap: () => Go.to(const OwnerRevenueScreen()),
        ),
      ),
    ],
  );
}
