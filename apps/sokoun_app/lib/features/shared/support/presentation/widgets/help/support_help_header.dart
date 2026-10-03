part of '../../../imports.dart';

class SupportHelpHeader extends StatelessWidget {
  const SupportHelpHeader({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 12.h,
    children: [
      Row(
        spacing: 12.w,
        children: [
          Container(
            padding: EdgeInsets.all(12.r),
            decoration: BoxDecoration(
              color: workspace.isOwner
                  ? AppColors.goldPale
                  : AppColors.mintLight,
              borderRadius: BorderRadius.circular(16.r),
            ),
            child: Icon(
              workspace.isOwner
                  ? Icons.real_estate_agent_outlined
                  : Icons.support_agent_rounded,
              color: workspace.isOwner
                  ? AppColors.sokoonGold
                  : AppColors.sokoonTeal,
              size: 28.r,
            ),
          ),
          Expanded(
            child: AppText(
              workspace.isOwner
                  ? LocaleKeys.supportOwnerIntro
                  : LocaleKeys.supportTenantIntro,
              style: AppTextStyles.regular14.copyWith(
                color: AppColors.sokoonGray,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
      SokounAdaptiveGrid(
        minimumWidth: 220,
        maximumColumns: 2,
        gap: 12,
        children: [
          DefaultButton(
            title: LocaleKeys.supportNewTicket,
            onTap: () => Go.to(SupportNewTicketScreen(workspace: workspace)),
          ),
          DefaultButton(
            title: LocaleKeys.supportMyTickets,
            color: AppColors.white,
            textColor: AppColors.sokoonNavy,
            onTap: () => Go.to(SupportTicketsScreen(workspace: workspace)),
          ),
        ],
      ),
    ],
  ).paddingAll(20);
}
