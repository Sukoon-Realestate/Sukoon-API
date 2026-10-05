part of '../../../imports.dart';

class OwnerPropertyStatusBadge extends StatelessWidget {
  const OwnerPropertyStatusBadge({super.key, required this.status});

  final OwnerPropertyStatus status;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: context.appColor(status.backgroundColor, surface: true),
        borderRadius: BorderRadius.circular(999.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        spacing: 4.w,
        children: [
          Icon(
            status.icon,
            color: context.appColor(status.foregroundColor),
            size: 12.r,
          ),
          Flexible(
            child: AppText(
              status.label,
              style: AppTextStyles.bold12.copyWith(
                color: context.appColor(status.foregroundColor),
                fontSize: 12.sp,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
