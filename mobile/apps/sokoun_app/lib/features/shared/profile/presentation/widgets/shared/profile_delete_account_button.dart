part of '../../../imports.dart';

class ProfileDeleteAccountButton extends StatelessWidget {
  const ProfileDeleteAccountButton({super.key});
  @override
  Widget build(BuildContext context) => DefaultButton(
    title: LocaleKeys.deleteAccount,
    color: context.appColor(AppColors.white, surface: true),
    textColor: context.appColor(AppColors.sokoonRose),
    borderColor: AppColors.roseAlpha07,
    onTap: () => Go.to(const ProfileDeleteAccountScreen()),
  );
}
