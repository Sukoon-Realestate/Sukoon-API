part of '../../../imports.dart';

class OwnerAnalyticsEmptyState extends StatelessWidget {
  const OwnerAnalyticsEmptyState({super.key});
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
        LocaleKeys.ownerAnalyticsEmptyTitle,
        style: AppTextStyles.bold16,
        textAlign: TextAlign.center,
      ),
    ],
  );
}
