part of '../../../imports.dart';

class OwnerPropertyActionSheet extends StatelessWidget {
  const OwnerPropertyActionSheet({super.key, required this.property});

  final OwnerPropertyContent property;

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Container(
        padding: EdgeInsets.fromLTRB(20.w, 10.h, 20.w, 24.h),
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(28.r)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 42.w,
                height: 4.h,
                decoration: BoxDecoration(
                  color: AppColors.graySoft,
                  borderRadius: BorderRadius.circular(99.r),
                ),
              ),
            ),
            18.szH,
            AppText(
              LocaleKeys.ownerPropertiesOptions,
              color: AppColors.sokoonNavy,
              fontSize: 20.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
            ),
            16.szH,
            for (final action in OwnerPropertyAction.values) ...[
              _OwnerPropertyActionRow(
                action: action,
                property: property,
                onPressed: () => Go.back(action),
              ),
              if (!action.isDelete) 10.szH,
            ],
          ],
        ),
      ),
    );
  }
}

class _OwnerPropertyActionRow extends StatelessWidget {
  const _OwnerPropertyActionRow({
    required this.action,
    required this.property,
    required this.onPressed,
  });

  final OwnerPropertyAction action;
  final OwnerPropertyContent property;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.white,
      borderRadius: BorderRadius.circular(16.r),
      child: InkWell(
        key: ValueKey('owner-property-action-${action.name}'),
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16.r),
        child: Container(
          padding: EdgeInsets.all(12.w),
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.sokoonBorder),
            borderRadius: BorderRadius.circular(16.r),
          ),
          child: Row(
            children: [
              Container(
                width: 42.r,
                height: 42.r,
                decoration: BoxDecoration(
                  color: action.backgroundColor,
                  borderRadius: BorderRadius.circular(12.r),
                ),
                child: Icon(
                  action.icon,
                  color: action.foregroundColor,
                  size: 22.r,
                ),
              ),
              12.szW,
              Expanded(
                child: AppText(
                  action.label(isHidden: property.status.isHidden),
                  color: action.foregroundColor,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w800,
                ),
              ),
              Icon(
                Icons.arrow_back_ios_new_rounded,
                color: AppColors.sokoonMuted,
                size: 16.r,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
