part of '../../../imports.dart';

class OwnerPropertyTopBar extends StatelessWidget {
  const OwnerPropertyTopBar({
    super.key,
    required this.title,
    this.showBackButton = true,
    this.trailing,
  });

  final String title;
  final bool showBackButton;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(16.w, 8.h, 16.w, 10.h),
      child: Row(
        children: [
          SizedBox(
            width: 44.r,
            height: 44.r,
            child: !showBackButton
                ? null
                : IconButton(
                    key: const ValueKey('owner-property-back'),
                    onPressed: Go.back,
                    icon: Icon(
                      Icons.arrow_forward_ios_rounded,
                      color: AppColors.sokoonNavy,
                      size: 20.r,
                    ),
                  ),
          ),
          Expanded(
            child: AppText(
              title,
              color: AppColors.sokoonNavy,
              fontSize: 20.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          SizedBox(width: 72.w, child: trailing ?? const SizedBox.shrink()),
        ],
      ),
    );
  }
}
