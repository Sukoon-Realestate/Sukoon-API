part of '../../../imports.dart';

class TenantVisitCard extends StatelessWidget {
  const TenantVisitCard({
    super.key,
    required this.visit,
    required this.onPressed,
    required this.onRatePressed,
    required this.onCancelPressed,
  });

  final TenantVisitContent visit;
  final VoidCallback onPressed;
  final VoidCallback onRatePressed;
  final VoidCallback onCancelPressed;

  Color get _statusColor {
    if (visit.status.isAccepted) {
      return AppColors.green;
    }
    if (visit.status.isPending) {
      return AppColors.amber;
    }
    return AppColors.red;
  }

  Color get _statusBackground {
    if (visit.status.isAccepted) {
      return AppColors.greenPale;
    }
    if (visit.status.isPending) {
      return AppColors.amberPale;
    }
    return AppColors.redPale;
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        key: ValueKey('tenant-visit-${visit.id}'),
        onTap: onPressed,
        borderRadius: BorderRadius.circular(18.r),
        child: Ink(
          padding: EdgeInsets.all(16.r),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(18.r),
            border: Border.all(color: AppColors.sokoonBorder),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        AppText(
                          visit.propertyTitle,
                          color: AppColors.sokoonNavy,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w900,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (visit.ownerName.isNotEmpty) ...[
                          3.szH,
                          AppText(
                            '${LocaleKeys.tenantVisitOwnerLabel} ${visit.ownerName}',
                            color: AppColors.sokoonGray,
                            fontSize: 12.sp,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                  10.szW,
                  Container(
                    padding: EdgeInsets.symmetric(
                      horizontal: 9.w,
                      vertical: 5.h,
                    ),
                    decoration: BoxDecoration(
                      color: _statusBackground,
                      borderRadius: BorderRadius.circular(999.r),
                    ),
                    child: AppText(
                      visit.resolvedStatusText,
                      color: _statusColor,
                      fontSize: 11.sp,
                      fontWeight: FontWeight.w900,
                      maxLines: 1,
                    ),
                  ),
                ],
              ),
              12.szH,
              Row(
                children: [
                  Icon(
                    Icons.calendar_today_outlined,
                    color: AppColors.sokoonGray,
                    size: 14.r,
                  ),
                  7.szW,
                  Expanded(
                    child: AppText(
                      visit.dateLabel,
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              12.szH,
              _VisitCardActions(
                visit: visit,
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
    required this.onRatePressed,
    required this.onCancelPressed,
  });

  final TenantVisitContent visit;
  final VoidCallback onRatePressed;
  final VoidCallback onCancelPressed;

  void _openChat() {
    Go.to(ChatThreadScreen(conversation: ChatContent.conversations.first));
  }

  void _findAlternative() => Go.to(const TenantSearchScreen());

  @override
  Widget build(BuildContext context) {
    if (visit.status.isAccepted) {
      return Row(
        children: [
          Expanded(
            child: _VisitCardAction(
              key: ValueKey('tenant-visit-chat-${visit.id}'),
              label: LocaleKeys.tenantVisitChatAction,
              backgroundColor: AppColors.bluePale,
              foregroundColor: AppColors.blue,
              onPressed: _openChat,
            ),
          ),
          8.szW,
          Expanded(
            child: _VisitCardAction(
              key: ValueKey('tenant-visit-rate-${visit.id}'),
              label: LocaleKeys.tenantVisitRateAction,
              backgroundColor: AppColors.goldPale,
              foregroundColor: AppColors.gold,
              onPressed: onRatePressed,
            ),
          ),
        ],
      );
    }

    if (visit.status.isPending) {
      return _VisitCardAction(
        key: ValueKey('tenant-visit-cancel-${visit.id}'),
        label: LocaleKeys.tenantVisitCancelRequest,
        backgroundColor: AppColors.redPale,
        foregroundColor: AppColors.red,
        onPressed: onCancelPressed,
      );
    }

    return _VisitCardAction(
      key: ValueKey('tenant-visit-alternative-${visit.id}'),
      label: LocaleKeys.tenantVisitFindAlternative,
      backgroundColor: AppColors.sokoonTeal,
      foregroundColor: AppColors.white,
      onPressed: _findAlternative,
    );
  }
}

class _VisitCardAction extends StatelessWidget {
  const _VisitCardAction({
    super.key,
    required this.label,
    required this.backgroundColor,
    required this.foregroundColor,
    required this.onPressed,
  });

  final String label;
  final Color backgroundColor;
  final Color foregroundColor;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 38.h,
      child: FilledButton(
        onPressed: onPressed,
        style: FilledButton.styleFrom(
          elevation: 0,
          backgroundColor: backgroundColor,
          foregroundColor: foregroundColor,
          padding: EdgeInsets.symmetric(horizontal: 8.w),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12.r),
          ),
        ),
        child: AppText(
          label,
          color: foregroundColor,
          fontSize: 12.sp,
          fontWeight: FontWeight.w900,
          maxLines: 1,
        ),
      ),
    );
  }
}
