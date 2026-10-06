part of '../../../imports.dart';

class TenantVisitCard extends StatelessWidget {
  const TenantVisitCard({
    super.key,
    required this.visit,
    this.isCanceling = false,
    this.canStartCancellation = true,
    required this.onPressed,
    required this.onRatePressed,
    required this.onCancelPressed,
  });

  final TenantVisitContent visit;
  final bool isCanceling;
  final bool canStartCancellation;
  final VoidCallback onPressed;
  final VoidCallback onRatePressed;
  final VoidCallback onCancelPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(18.r),
        child: Ink(
          padding: EdgeInsets.all(16.r),
          decoration: BoxDecoration(
            color: context.appColor(AppColors.white, surface: true),
            borderRadius: BorderRadius.circular(18.r),
            border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 12.h,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 10.w,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      spacing: 3.h,
                      children: [
                        AppText(
                          visit.propertyTitle,
                          style: AppTextStyles.bold14.copyWith(
                            color: context.appColor(AppColors.sokoonNavy),
                            fontSize: 14.sp,
                            height: 1.45,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (visit.ownerName.isNotEmpty)
                          AppText(
                            '${LocaleKeys.tenantVisitOwnerLabel} ${visit.ownerName}',
                            style: AppTextStyles.regular12.copyWith(
                              color: context.appColor(AppColors.sokoonGray),
                              fontSize: 12.sp,
                              height: 1.45,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                      ],
                    ),
                  ),
                  Container(
                    padding: EdgeInsets.symmetric(
                      horizontal: 9.w,
                      vertical: 5.h,
                    ),
                    decoration: BoxDecoration(
                      color: context.appColor(
                        visit.status.backgroundColor,
                        surface: true,
                      ),
                      borderRadius: BorderRadius.circular(999.r),
                    ),
                    child: AppText(
                      visit.resolvedStatusText,
                      style: AppTextStyles.bold11.copyWith(
                        color: context.appColor(visit.status.foregroundColor),
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                    ),
                  ),
                ],
              ),
              Row(
                spacing: 7.w,
                children: [
                  Icon(
                    Icons.calendar_today_outlined,
                    color: context.appColor(AppColors.sokoonGray),
                    size: 14.r,
                  ),
                  Expanded(
                    child: AppText(
                      visit.dateLabel,
                      style: AppTextStyles.regular12.copyWith(
                        color: context.appColor(AppColors.sokoonGray),
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              _VisitCardActions(
                visit: visit,
                isCanceling: isCanceling,
                canStartCancellation: canStartCancellation,
                onRatePressed: onRatePressed,
                onCancelPressed: onCancelPressed,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _VisitCardActions extends StatelessWidget {
  const _VisitCardActions({
    required this.visit,
    this.isCanceling = false,
    this.canStartCancellation = true,
    required this.onRatePressed,
    required this.onCancelPressed,
  });

  final TenantVisitContent visit;
  final bool isCanceling;
  final bool canStartCancellation;
  final VoidCallback onRatePressed;
  final VoidCallback onCancelPressed;

  void _openChat() {
    if (visit.ownerId.isEmpty) return;
    Go.to(StartConversationScreen(userId: visit.ownerId));
  }

  void _findAlternative() => Go.to(const TenantSearchScreen());

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8.w,
      runSpacing: 8.h,
      children: [
        if (visit.canChat)
          _VisitCardAction(
            label: LocaleKeys.tenantVisitChatAction,
            backgroundColor: context.appColor(
              AppColors.bluePale,
              surface: true,
            ),
            foregroundColor: context.appColor(AppColors.blue),
            onPressed: _openChat,
          ),
        if (visit.canReview)
          _VisitCardAction(
            label: LocaleKeys.tenantVisitRateAction,
            backgroundColor: context.appColor(
              AppColors.goldPale,
              surface: true,
            ),
            foregroundColor: context.appColor(AppColors.brown),
            onPressed: onRatePressed,
          ),
        if (visit.canCancel)
          _VisitCardAction(
            label: LocaleKeys.tenantVisitCancelRequest,
            backgroundColor: context.appColor(AppColors.redPale, surface: true),
            foregroundColor: context.appColor(AppColors.sokoonRose),
            isLoading: isCanceling,
            onPressed: canStartCancellation ? onCancelPressed : null,
          ),
        if (visit.canFindAlternative)
          _VisitCardAction(
            label: LocaleKeys.tenantVisitFindAlternative,
            backgroundColor: context.appColor(
              AppColors.sokoonTeal,
              surface: true,
            ),
            foregroundColor: AppColors.white,
            onPressed: _findAlternative,
          ),
      ],
    );
  }
}

class _VisitCardAction extends StatelessWidget {
  const _VisitCardAction({
    required this.label,
    this.isLoading = false,
    required this.backgroundColor,
    required this.foregroundColor,
    required this.onPressed,
  });

  final String label;
  final bool isLoading;
  final Color backgroundColor;
  final Color foregroundColor;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(minHeight: 48),
      child: FilledButton(
        onPressed: onPressed,
        style: FilledButton.styleFrom(
          elevation: 0,
          backgroundColor: context.appColor(backgroundColor, surface: true),
          foregroundColor: context.appColor(foregroundColor),
          padding: EdgeInsets.symmetric(horizontal: 8.w),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12.r),
          ),
        ),
        child: isLoading
            ? SizedBox.square(
                dimension: 20.r,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: context.appColor(foregroundColor),
                ),
              )
            : AppText(
                label,
                style: AppTextStyles.bold12.copyWith(
                  color: context.appColor(foregroundColor),
                  fontSize: 12.sp,
                  height: 1.45,
                ),
              ),
      ),
    );
  }
}
