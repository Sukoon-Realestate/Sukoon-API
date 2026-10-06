part of '../../../imports.dart';

class SupportTicketDetailContentView extends StatelessWidget {
  const SupportTicketDetailContentView({
    super.key,
    required this.id,
    required this.workspace,
    required this.onRetry,
  });

  final String id;
  final AppWorkspace workspace;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Expanded(
        child:
            StatusBuilder<SupportTicketCubit, SupportTicketContent>.withShimmer(
              initialDataForShimmer: const SupportTicketContent.initial(),
              onRetry: onRetry,
              builder: (ticket) =>
                  SupportTicketThread(ticket: ticket, workspace: workspace),
            ),
      ),
      BlocBuilder<SupportTicketCubit, AsyncState<SupportTicketContent>>(
        builder: (context, state) => widgets.Visibility(
          visible: state.data.canReply,
          maintainState: true,
          child: SupportTicketReply(
            id: id,
            workspace: workspace,
            enabled: state.isSuccess && state.data.canReply,
            onTicketUpdated: context.read<SupportTicketCubit>().apply,
          ),
        ),
      ),
    ],
  );
}
