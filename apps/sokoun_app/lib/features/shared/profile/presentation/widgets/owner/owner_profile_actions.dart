part of '../../../imports.dart';

class OwnerProfileActions extends StatelessWidget {
  const OwnerProfileActions({super.key});

  @override
  Widget build(BuildContext context) => ProfileSurfaceCard(
    child: ProfileMenuTile(
      icon: Icons.account_balance_wallet_outlined,
      label: LocaleKeys.ownerRevenueTitle,
      iconColor: AppColors.sokoonTeal,
      iconBackgroundColor: AppColors.mintLight,
      onTap: () => Go.to(const OwnerRevenueScreen()),
    ),
  );
}
