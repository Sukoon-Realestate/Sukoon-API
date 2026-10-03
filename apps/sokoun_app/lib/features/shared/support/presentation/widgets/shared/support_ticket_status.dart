part of '../../../imports.dart';

class SupportTicketStatus extends StatelessWidget {
  const SupportTicketStatus({super.key, required this.ticket});
  final SupportTicketContent ticket;
  @override
  Widget build(BuildContext context) {
    final Color color = ticket.isResolved
        ? AppColors.green
        : ticket.isWaiting
        ? AppColors.blue
        : ticket.status == SupportTicketState.open
        ? AppColors.sokoonTeal
        : AppColors.sokoonGray;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 5.h),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .08),
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
          color: ticket.isResolved ? AppColors.sokoonTeal : color,
        ),
      ),
    );
  }
}
