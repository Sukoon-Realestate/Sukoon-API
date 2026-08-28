part of '../../../imports.dart';

class OwnerPropertyStatusBadge extends StatelessWidget {
  const OwnerPropertyStatusBadge({super.key, required this.status});

  final OwnerPropertyStatus status;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: status.backgroundColor,
        borderRadius: BorderRadius.circular(999.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(status.icon, color: status.foregroundColor, size: 12.r),
          4.szW,
          AppText(
            status.label,
            color: status.foregroundColor,
            fontSize: 12.sp,
            fontWeight: FontWeight.w700,
          ),
        ],
      ),
    );
  }
}
