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
  final GlobalKey _replyFieldKey = GlobalKey();
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
    if (!widget.enabled || _cubit.isLoading) {
      return;
    }
    final String submittedBody = _controller.text;
    final SupportTicketContent? ticket = await _cubit.reply(
      id: widget.id,
      body: submittedBody,
      workspace: widget.workspace,
    );
    if (!context.mounted) return;
    if (ticket == null) {
      if (_cubit.state.isSuccess && _cubit.state.msg?.isNotEmpty == true) {
        Messages.showToast(msg: _cubit.state.msg!, status: BaseStatus.error);
      }
      return;
    }
    if (_controller.text == submittedBody) _controller.clear();
    widget.onTicketUpdated(ticket);
  }

  List<FirstValidationErrorField> _validationFields() => [
    FirstValidationErrorField(
      fieldKey: _replyFieldKey,
      title: LocaleKeys.supportReplyHint,
      value: _controller.text,
      validator: Validators.validateRequired,
    ),
  ];

  @override
  Widget build(BuildContext context) => UnsavedChangesGuard(
    hasChanges: () => _controller.text.trim().isNotEmpty,
    isSaving: () => _cubit.isLoading,
    child: FirstValidationErrorForm(
      validationFields: _validationFields,
      onValid: () => _send(context),
      builder: (context, submit) => SokounActionFooter(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          spacing: 10.h,
          children: [
            BlocBuilder<SupportReplyCubit, AsyncState<SupportTicketContent>>(
              bloc: _cubit,
              builder: (context, state) => DefaultTextField(
                key: _replyFieldKey,
                readOnly: !widget.enabled || state.isLoading,
                controller: _controller,
                title: LocaleKeys.supportReplyHint,
                maxLength: 4000,
                minLines: 1,
                maxLines: 3,
                inputType: TextInputType.multiline,
                validator: Validators.validateRequired,
              ),
            ),
            widget.enabled
                ? AppLoadingButton(
                    asyncCall: (_) => submit(),
                    title: LocaleKeys.supportSendReply,
                  )
                : DefaultButton(
                    title: LocaleKeys.supportSendReply,
                    disabled: true,
                  ),
          ],
        ),
      ),
    ),
  );
}
