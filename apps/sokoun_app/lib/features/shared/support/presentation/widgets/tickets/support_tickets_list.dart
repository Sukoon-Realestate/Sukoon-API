part of '../../../imports.dart';

class SupportTicketsList extends StatefulWidget {
  const SupportTicketsList({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  State<SupportTicketsList> createState() => _SupportTicketsListState();
}

class _SupportTicketsListState extends State<SupportTicketsList> {
  final PagifyController<SupportTicketContent> _controller =
      PagifyController<SupportTicketContent>();
  @override
  Widget build(BuildContext context) => AppPagify<SupportTicketContent>(
    pagifyController: _controller,
    enablePullRefresh: true,
    shrinkWrap: false,
    contentPadding: EdgeInsets.all(20.r),
    asyncCall: (_, page) =>
        SupportTicketsData.getPage(page: page, workspace: widget.workspace),
    cacheKey: SupportTicketsData.cacheKey(widget.workspace),
    cachePolicy: ReadCachePolicy.privateMemory,
    cacheToJson: (ticket) => ticket.toJson(),
    cacheFromJson: SupportTicketContent.fromJson,
    emptyListView: SupportTicketsEmptyState(workspace: widget.workspace),
    header: TextButton.icon(
      icon: const Icon(Icons.add_rounded),
      label: AppText(LocaleKeys.supportNewTicket, style: AppTextStyles.bold14),
      onPressed: () async {
        await Go.to(SupportNewTicketScreen(workspace: widget.workspace));
        if (mounted) _controller.refresh();
      },
    ),
    errorBuilder: (error) =>
        ExceptionView(msg: error.msg, onRetry: () async => _controller.retry()),
    itemBuilder: (_, __, ___, ticket) => SupportTicketCard(
      key: ValueKey(ticket.id),
      ticket: ticket,
      workspace: widget.workspace,
      onReturn: () {
        if (mounted) _controller.refresh();
      },
    ),
  );
}
