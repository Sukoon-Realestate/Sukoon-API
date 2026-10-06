part of '../../../imports.dart';

class OwnerRevenueEmptyState extends StatelessWidget {
  const OwnerRevenueEmptyState({super.key});
  @override
  Widget build(BuildContext context) => Column(
    children: [
      ExcludeSemantics(
        child: Assets.lottie.noData.lottie(
          width: 140.r,
          height: 116.r,
          animate: !MediaQuery.disableAnimationsOf(context),
          repeat: false,
          package: 'melos_core',
        ),
      ),
      AppText(
        LocaleKeys.ownerRevenueEmptyTitle,
        style: AppTextStyles.bold16,
        textAlign: TextAlign.center,
      ),
      8.szH,
      AppText(
        LocaleKeys.ownerRevenueEmptyDescription,
        style: AppTextStyles.regular13,
        textAlign: TextAlign.center,
      ),
    ],
  );
}
