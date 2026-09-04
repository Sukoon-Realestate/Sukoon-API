part of '../../../imports.dart';

class ProfileScreenHeader extends StatelessWidget {
  const ProfileScreenHeader({
    super.key,
    required this.title,
    this.showBackButton = false,
    this.trailing,
  });

  final String title;
  final bool showBackButton;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(minHeight: 58.h),
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 8.h),
      decoration: showBackButton
          ? const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
            )
          : null,
      child: Row(
        children: [
          if (showBackButton)
            IconButton(
              key: const ValueKey('profile-back'),
              onPressed: Go.back,
              icon: Icon(
                Icons.arrow_forward_rounded,
                color: AppColors.sokoonNavy,
                size: 22.r,
              ),
            )
          else
            const SizedBox.shrink(),
          Expanded(
            child: AppText(
              title,
              color: AppColors.sokoonNavy,
              fontSize: showBackButton ? 17.sp : 21.sp,
              fontWeight: FontWeight.w900,
              textAlign: showBackButton ? TextAlign.center : TextAlign.start,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (trailing != null) trailing! else if (showBackButton) 48.szW,
        ],
      ),
    );
  }
}
