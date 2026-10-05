part of '../../../imports.dart';

class SupportTicketStatus extends StatelessWidget {
  const SupportTicketStatus({super.key, required this.ticket});
  final SupportTicketContent ticket;
  @override
  Widget build(BuildContext context) {
    final Color color = ticket.isResolved
        ? context.appColor(AppColors.green)
        : ticket.isWaiting
        ? context.appColor(AppColors.blue)
        : ticket.status == SupportTicketState.open
        ? context.appColor(AppColors.sokoonTeal)
        : context.appColor(AppColors.sokoonGray);
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 5.h),
      decoration: BoxDecoration(
        color: context.appColor(color, surface: true).withValues(alpha: .08),
        borderRadius: BorderRadius.circular(99.r),
      ),
      child: AppText(
        ticket.isResolved
            ? LocaleKeys.supportStatusResolved
            : ticket.isWaiting
            ? LocaleKeys.supportStatusWaiting
            : ticket.status == SupportTicketState.open
            ? LocaleKeys.supportStatusOpen
            : LocaleKeys.supportStatusUnknown,
        style: AppTextStyles.bold12.copyWith(
          color: ticket.isResolved
              ? context.appColor(AppColors.sokoonTeal)
              : color,
        ),
      ),
    );
  }
}
