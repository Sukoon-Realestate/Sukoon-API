part of '../../../imports.dart';

class SupportTicketForm extends StatefulWidget {
  const SupportTicketForm({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  State<SupportTicketForm> createState() => _SupportTicketFormState();
}

class _SupportTicketFormState extends State<SupportTicketForm> {
  final GlobalKey _subjectFieldKey = GlobalKey();
  final GlobalKey _descriptionFieldKey = GlobalKey();
  final TextEditingController _subject = TextEditingController();
  final TextEditingController _description = TextEditingController();
  late final SupportTicketSubmitCubit _cubit;
  late final ValueNotifier<SupportTicketBody> _body;
  bool _submitted = false;
  @override
  void initState() {
    super.initState();
    _cubit = SupportTicketSubmitCubit();
    _body = ValueNotifier(
      SupportTicketBody.initial(workspace: widget.workspace),
    );
  }

  @override
  void dispose() {
    _cubit.close();
    _body.dispose();
    _subject.dispose();
    _description.dispose();
    super.dispose();
  }

  Future<void> _submit(BuildContext context) async {
    if (_cubit.isLoading) {
      return;
    }
    FocusScope.of(context).unfocus();
    final SupportTicketContent? ticket = await _cubit.submit(_body.value);
    if (!context.mounted) return;
    if (ticket == null) {
      if (_cubit.state.isSuccess && _cubit.state.msg?.isNotEmpty == true) {
        Messages.showToast(msg: _cubit.state.msg!, status: BaseStatus.error);
      }
      return;
    }
    _submitted = true;
    Go.off(
      SupportTicketDetailScreen(id: ticket.id, workspace: widget.workspace),
    );
  }

  String? _validate(String? value, int minimum) =>
      (value?.trim().length ?? 0) < minimum
      ? LocaleKeys.supportFieldMinimum.replaceAll('{min}', '$minimum')
      : null;

  List<FirstValidationErrorField> _validationFields() => [
    FirstValidationErrorField(
      fieldKey: _subjectFieldKey,
      title: LocaleKeys.supportSubject,
      value: _subject.text,
      validator: (value) => _validate(value, 3),
    ),
    FirstValidationErrorField(
      fieldKey: _descriptionFieldKey,
      title: LocaleKeys.supportDetails,
      value: _description.text,
      validator: (value) => _validate(value, 10),
    ),
  ];
  @override
  Widget build(BuildContext context) => BlocProvider.value(
    value: _cubit,
    child: UnsavedChangesGuard(
      hasChanges: () => !_submitted && _body.value.hasChanges,
      isSaving: () => _cubit.isLoading,
      child: FirstValidationErrorForm(
        validationFields: _validationFields,
        onValid: () => _submit(context),
        builder: (context, submit) => Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: EdgeInsets.all(20.r),
                child:
                    BlocBuilder<
                      SupportTicketSubmitCubit,
                      AsyncState<SupportTicketContent>
                    >(
                      builder: (context, state) => AbsorbPointer(
                        absorbing: state.isLoading,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          spacing: 18.h,
                          children: [
                            AppText(
                              LocaleKeys.supportTicketIntro,
                              style: AppTextStyles.regular14.copyWith(
                                color: AppColors.sokoonGray,
                                height: 1.5,
                              ),
                            ),
                            AppText(
                              LocaleKeys.supportIssueType,
                              style: AppTextStyles.bold14,
                            ),
                            ValueListenableBuilder<SupportTicketBody>(
                              valueListenable: _body,
                              builder: (context, body, _) => Wrap(
                                spacing: 8.w,
                                runSpacing: 8.h,
                                children: [
                                  for (final topic in SupportTopic.forWorkspace(
                                    widget.workspace,
                                  ))
                                    SokounSelectionChip(
                                      label: topic.label,
                                      selected: body.topic == topic,
                                      onPressed: () => _body.value = body
                                          .copyWith(topic: topic),
                                    ),
                                ],
                              ),
                            ),
                            DefaultTextField.withTitle(
                              key: _subjectFieldKey,
                              controller: _subject,
                              upperTitle: LocaleKeys.supportSubject,
                              title: LocaleKeys.supportSubjectHint,
                              maxLength: 160,
                              action: TextInputAction.next,
                              validator: (value) => _validate(value, 3),
                              onChanged: (value) => _body.value = _body.value
                                  .copyWith(subject: value ?? ''),
                            ),
                            DefaultTextField.withTitle(
                              key: _descriptionFieldKey,
                              controller: _description,
                              upperTitle: LocaleKeys.supportDetails,
                              title: LocaleKeys.supportDetailsHint,
                              maxLength: 4000,
                              minLines: 4,
                              maxLines: 8,
                              inputType: TextInputType.multiline,
                              validator: (value) => _validate(value, 10),
                              onChanged: (value) => _body.value = _body.value
                                  .copyWith(description: value ?? ''),
                            ),
                            ValueListenableBuilder<SupportTicketBody>(
                              valueListenable: _body,
                              builder: (context, body, _) =>
                                  SupportTicketAttachments(
                                    files: body.attachments,
                                    onChanged: (files) => _body.value = body
                                        .copyWith(attachments: files),
                                  ),
                            ),
                          ],
                        ),
                      ),
                    ),
              ),
            ),
            SokounActionFooter(
              width: SokounContentWidth.form,
              child: AppLoadingButton(
                asyncCall: (_) => submit(),
                title: LocaleKeys.supportSendTicket,
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
