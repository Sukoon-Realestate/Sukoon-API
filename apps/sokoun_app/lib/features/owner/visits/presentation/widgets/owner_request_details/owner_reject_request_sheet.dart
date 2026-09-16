part of '../../../imports.dart';

class OwnerRejectRequestSheet extends StatefulWidget {
  const OwnerRejectRequestSheet({super.key});

  @override
  State<OwnerRejectRequestSheet> createState() =>
      _OwnerRejectRequestSheetState();
}

class _OwnerRejectRequestSheetState extends State<OwnerRejectRequestSheet> {
  OwnerRejectionReason _selectedReason = OwnerRejectionReason.inconvenientTime;

  void _selectReason(OwnerRejectionReason reason) {
    setState(() => _selectedReason = reason);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(24.w, 12.h, 24.w, 28.h),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const _OwnerSheetHandle(),
          18.szH,
          _OwnerDecisionSheetHeader(
            icon: Icons.close_rounded,
            title: LocaleKeys.ownerRejectTitle,
            subtitle: LocaleKeys.ownerRejectSubtitle,
            iconColor: AppColors.red,
            iconBackgroundColor: AppColors.redPale,
          ),
          18.szH,
          for (final OwnerRejectionReason reason
              in OwnerRejectionReason.values) ...[
            _OwnerRejectionReasonTile(
              reason: reason,
              isSelected: reason.isSame(_selectedReason),
              onPressed: () => _selectReason(reason),
            ),
            if (!reason.isOther) 8.szH,
          ],
          18.szH,
          DefaultButton(
            onTap: () => Go.back(_selectedReason),
            title: LocaleKeys.ownerRejectConfirm,
            color: AppColors.red,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            fontSize: 15.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    );
  }
}

class _OwnerRejectionReasonTile extends StatelessWidget {
  const _OwnerRejectionReasonTile({
    required this.reason,
    required this.isSelected,
    required this.onPressed,
  });

  final OwnerRejectionReason reason;
  final bool isSelected;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(12.r),
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(
              color: isSelected ? AppColors.red : AppColors.sokoonBorder,
              width: 1.5,
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 20.r,
                height: 20.r,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: isSelected ? AppColors.red : AppColors.white,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: isSelected ? AppColors.red : AppColors.sokoonBorder,
                    width: 2,
                  ),
                ),
                child: isSelected
                    ? Container(
                        width: 8.r,
                        height: 8.r,
                        decoration: const BoxDecoration(
                          color: AppColors.white,
                          shape: BoxShape.circle,
                        ),
                      )
                    : null,
              ),
              12.szW,
              Expanded(
                child: AppText(
                  reason.label,
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
