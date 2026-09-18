part of '../../../imports.dart';

class OwnerPropertiesHeader extends StatelessWidget {
  const OwnerPropertiesHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return AppText(
      LocaleKeys.ownerPropertiesTitle,
      color: AppColors.sokoonNavy,
      fontSize: 20.sp,
      fontWeight: FontWeight.w900,
      textAlign: TextAlign.start,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
    );
  }
}
