part of '../../../imports.dart';

class SupportTicketReply extends StatefulWidget {
  const SupportTicketReply({
    super.key,
    required this.id,
    required this.workspace,
    required this.onTicketUpdated,
    required this.enabled,
  });
  final bool enabled;
  final String id;
  final AppWorkspace workspace;
  final ValueChanged<SupportTicketContent> onTicketUpdated;
  @override
  State<SupportTicketReply> createState() => _SupportTicketReplyState();
}

class _SupportTicketReplyState extends State<SupportTicketReply> {
  final TextEditingController _controller = TextEditingController();
  late final SupportReplyCubit _cubit;
  @override
  void initState() {
    super.initState();
    _cubit = context.read<SupportReplyCubit>();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send(BuildContext context) async {
    if (!widget.enabled ||
        _cubit.isLoading ||
        _controller.text.trim().isEmpty) {
      return;
    }
    final String submittedBody = _controller.text;
    FocusScope.of(context).unfocus();
    final SupportTicketContent? ticket = await _cubit.reply(
      id: widget.id,
      body: submittedBody,
      workspace: widget.workspace,
    );
    if (!context.mounted) return;
    if (ticket == null) {
      if (_cubit.state.isSuccess) {
        MessageUtils.showSnackBar(
          LocaleKeys.supportInvalidResponse,
          context: context,
        );
      }
      return;
    }
    if (_controller.text == submittedBody) _controller.clear();
    widget.onTicketUpdated(ticket);
  }

  @override
  Widget build(BuildContext context) => UnsavedChangesGuard(
    hasChanges: () => _controller.text.trim().isNotEmpty,
    isSaving: () => _cubit.isLoading,
    child: SokounActionFooter(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        spacing: 10.h,
        children: [
          BlocBuilder<SupportReplyCubit, AsyncState<SupportTicketContent>>(
            bloc: _cubit,
            builder: (context, state) => DefaultTextField(
              readOnly: !widget.enabled || state.isLoading,
              controller: _controller,
              title: LocaleKeys.supportReplyHint,
              maxLength: 4000,
              minLines: 1,
              maxLines: 3,
              inputType: TextInputType.multiline,
            ),
          ),
          widget.enabled
              ? AppLoadingButton(
                  asyncCall: _send,
                  title: LocaleKeys.supportSendReply,
                )
              : DefaultButton(
                  title: LocaleKeys.supportSendReply,
                  disabled: true,
                ),
        ],
      ),
    ),
  );
}
