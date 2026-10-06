part of '../../../imports.dart';

class ProfileAccountDetailRow extends StatelessWidget {
  const ProfileAccountDetailRow({
    super.key,
    required this.label,
    required this.value,
    this.valueDirection,
  });
  final String label;
  final String value;
  final TextDirection? valueDirection;

  @override
  Widget build(BuildContext context) {
    final labelText = AppText(
      label,
      style: AppTextStyles.regular12.copyWith(
        color: context.appColor(AppColors.sokoonGray),
        height: 1.45,
      ),
    );
    final valueText = SelectableText(
      value,
      textDirection: valueDirection,
      textAlign: Directionality.of(context) == TextDirection.rtl
          ? TextAlign.right
          : TextAlign.left,
      style: AppTextStyles.bold14.copyWith(
        color: context.appColor(AppColors.sokoonNavy),
        height: 1.45,
      ),
    );
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 280 ||
            MediaQuery.textScalerOf(context).scale(14) > 18.2) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 6.h,
            children: [labelText, valueText],
          );
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 12.w,
          children: [
            Expanded(flex: 3, child: valueText),
            Flexible(flex: 2, child: labelText),
          ],
        );
      },
    );
  }
}
