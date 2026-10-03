part of '../../../imports.dart';

class SupportTicketThread extends StatelessWidget {
  const SupportTicketThread({
    super.key,
    required this.ticket,
    required this.workspace,
  });
  final SupportTicketContent ticket;
  final AppWorkspace workspace;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Expanded(
        child: ListView(
          padding: EdgeInsets.all(20.r),
          children: [
            Wrap(
              spacing: 12.w,
              runSpacing: 8.h,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                AppText(
                  ticket.reference,
                  style: AppTextStyles.regular14.copyWith(
                    color: AppColors.sokoonGray,
                  ),
                ),
                SupportTicketStatus(ticket: ticket),
              ],
            ),
            12.szH,
            AppText(
              ticket.subject,
              style: AppTextStyles.bold16.copyWith(color: AppColors.sokoonNavy),
            ),
            20.szH,
            if (ticket.messages.isEmpty) const SupportMessagesEmptyState(),
            for (final message in ticket.messages)
              SupportMessageBubble(key: ValueKey(message.id), message: message),
            if (ticket.isResolved)
              AppText(
                LocaleKeys.supportResolvedNotice,
                style: AppTextStyles.regular14.copyWith(
                  color: AppColors.sokoonTeal,
                  height: 1.5,
                ),
              ),
            if (ticket.isResolved) ...[
              16.szH,
              DefaultButton(
                title: LocaleKeys.supportNewTicket,
                onTap: () =>
                    Go.to(SupportNewTicketScreen(workspace: workspace)),
              ),
            ],
          ],
        ),
      ),
    ],
  );
}
