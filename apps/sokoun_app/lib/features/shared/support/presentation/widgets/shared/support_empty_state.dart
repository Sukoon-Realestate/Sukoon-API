part of '../../../imports.dart';

class SupportFaqEmptyState extends StatelessWidget {
  const SupportFaqEmptyState({
    super.key,
    this.isSearching = false,
    this.onClear,
  });
  final bool isSearching;
  final VoidCallback? onClear;
  @override
  Widget build(BuildContext context) => _SupportEmptyView(
    title: isSearching
        ? LocaleKeys.supportSearchEmptyTitle
        : LocaleKeys.supportFaqEmptyTitle,
    description: isSearching
        ? LocaleKeys.supportSearchEmptyDescription
        : LocaleKeys.supportFaqEmptyDescription,
    action: isSearching
        ? TextButton(
            onPressed: onClear,
            child: AppText(
              LocaleKeys.supportClearSearch,
              style: AppTextStyles.bold14,
            ),
          )
        : null,
  );
}

class SupportTicketsEmptyState extends StatelessWidget {
  const SupportTicketsEmptyState({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => _SupportEmptyView(
    title: LocaleKeys.supportTicketsEmptyTitle,
    description: LocaleKeys.supportTicketsEmptyDescription,
    action: DefaultButton(
      title: LocaleKeys.supportNewTicket,
      onTap: () => Go.to(SupportNewTicketScreen(workspace: workspace)),
    ),
  );
}

class SupportMessagesEmptyState extends StatelessWidget {
  const SupportMessagesEmptyState({super.key});
  @override
  Widget build(BuildContext context) => _SupportEmptyView(
    title: LocaleKeys.supportMessagesEmptyTitle,
    description: LocaleKeys.supportMessagesEmptyDescription,
  );
}

class _SupportEmptyView extends StatelessWidget {
  const _SupportEmptyView({
    required this.title,
    required this.description,
    this.action,
  });
  final String title;
  final String description;
  final Widget? action;
  @override
  Widget build(BuildContext context) => Column(
    mainAxisSize: MainAxisSize.min,
    children: [
      ExcludeSemantics(
        child: Assets.lottie.noData.lottie(
          width: 132.r,
          height: 110.r,
          package: 'melos_core',
          repeat: false,
          animate:
              !MediaQuery.disableAnimationsOf(context) &&
              !MediaQuery.accessibleNavigationOf(context),
        ),
      ),
      12.szH,
      AppText(
        title,
        textAlign: TextAlign.center,
        style: AppTextStyles.bold16.copyWith(color: AppColors.sokoonNavy),
      ),
      8.szH,
      AppText(
        description,
        textAlign: TextAlign.center,
        style: AppTextStyles.regular14.copyWith(
          color: AppColors.sokoonGray,
          height: 1.5,
        ),
      ),
      if (action != null) ...[16.szH, action!],
    ],
  ).paddingAll(24);
}
