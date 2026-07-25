part of '../../../imports.dart';

class VisitHeader extends StatelessWidget {
  const VisitHeader({
    super.key,
    required this.title,
    required this.onBackPressed,
    this.backKey,
  });

  final String title;
  final VoidCallback onBackPressed;
  final Key? backKey;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 54.h,
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 14.w),
        child: Row(
          children: [
            IconButton(
              key: backKey,
              onPressed: onBackPressed,
              visualDensity: VisualDensity.compact,
              icon: Icon(
                Icons.arrow_back_ios_new_rounded,
                color: AppColors.sokoonNavy,
                size: 20.r,
              ),
            ),
            4.szW,
            Expanded(
              child: AppText(
                title,
                color: AppColors.sokoonNavy,
                fontSize: 20.sp,
                fontWeight: FontWeight.w900,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
