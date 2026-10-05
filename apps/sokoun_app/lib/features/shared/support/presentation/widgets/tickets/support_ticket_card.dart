part of '../../../imports.dart';

class SupportTicketCard extends StatelessWidget {
  const SupportTicketCard({
    super.key,
    required this.ticket,
    required this.workspace,
    required this.onReturn,
  });
  final SupportTicketContent ticket;
  final AppWorkspace workspace;
  final VoidCallback onReturn;
  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    color: context.appColor(AppColors.white, surface: true),
    surfaceTintColor: AppColors.transparent,
    elevation: 0,
    clipBehavior: Clip.antiAlias,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(16.r),
      side: BorderSide(color: context.appColor(AppColors.sokoonBorder)),
    ),
    child: InkWell(
      borderRadius: BorderRadius.circular(16.r),
      onTap: () async {
        await Go.to(
          SupportTicketDetailScreen(id: ticket.id, workspace: workspace),
        );
        onReturn();
      },
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: 8.h,
        children: [
          Wrap(
            spacing: 12.w,
            runSpacing: 6.h,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              AppText(
                ticket.reference.isEmpty ? ticket.id : ticket.reference,
                style: AppTextStyles.regular12.copyWith(
                  color: context.appColor(AppColors.sokoonGray),
                ),
              ),
              SupportTicketStatus(ticket: ticket),
            ],
          ),
          AppText(
            ticket.subject,
            style: AppTextStyles.bold16.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
            ),
          ),
          if (supportDate(ticket.createdAt, context).isNotEmpty)
            AppText(
              supportDate(ticket.createdAt, context),
              style: AppTextStyles.regular12.copyWith(
                color: context.appColor(AppColors.sokoonGray),
              ),
            ),
        ],
      ).paddingAll(16),
    ),
  ).paddingOnly(bottom: 10);
}

String supportDate(String value, BuildContext context) {
  final DateTime? date = DateTime.tryParse(value);
  return date == null
      ? ''
      : DateFormat.yMMMd(
          context.locale.languageCode,
        ).add_jm().format(date.toLocal());
}
