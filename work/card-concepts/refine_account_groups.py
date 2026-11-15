from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
p=root/'apps/sokoun_app/lib/shared_widgets/sokoun_settings_section.dart'
s=p.read_text()
s=s.replace('''    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: palette.surface,
        border: Border.all(color: palette.line),
        borderRadius: BorderRadius.circular(16),
      ),
      child: DefaultTextStyle.merge(''', '''    return Material(
      color: palette.surface,
      shape: RoundedRectangleBorder(
        side: BorderSide(color: palette.line),
        borderRadius: BorderRadius.circular(16),
      ),
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: DefaultTextStyle.merge(''')
s=s.replace('''      ),
    );
  }
}''','''        ),
      ),
    );
  }
}''')
p.write_text(s)
p=root/'apps/sokoun_app/lib/features/shared/support/presentation/widgets/new_ticket/support_ticket_form_content.dart'
s=p.read_text()
a=s.index('                              AppText(\n                                LocaleKeys.supportIssueType,')
b=s.index('                              DefaultTextField.withTitle(',a)
s=s[:a]+'''                              ValueListenableBuilder<SupportTicketBody>(
                                valueListenable: owner._body,
                                builder: (context, body, _) => Column(
                                  mainAxisSize: MainAxisSize.min,
                                  crossAxisAlignment: CrossAxisAlignment.stretch,
                                  children: [
                                    AppText(LocaleKeys.supportIssueType, style: AppTextStyles.bold14),
                                    const SizedBox(height: 8),
                                    Wrap(
                                      spacing: 8,
                                      runSpacing: 8,
                                      children: [
                                        for (final topic in SupportTopic.forWorkspace(owner.widget.workspace, scope: owner.widget.scope))
                                          ChoiceChip(
                                            label: Text(topic.label),
                                            showCheckmark: false,
                                            selected: body.topic == topic,
                                            selectedColor: SokounPalette.of(context).chip,
                                            backgroundColor: SokounPalette.of(context).surface,
                                            side: BorderSide(color: SokounPalette.of(context).line),
                                            labelStyle: Theme.of(context).textTheme.bodySmall?.copyWith(color: SokounPalette.of(context).text, height: 1.5),
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                                            onSelected: (_) => owner._body.value = body.copyWith(
                                              topic: topic,
                                              rentalContext: body.rentalContext.copyWith(
                                                paymentIssue: topic == SupportTopic.payment
                                                  ? body.rentalContext.paymentIssue : SupportPaymentIssue.general,
                                              ),
                                            ),
                                          ),
                                      ],
                                    ),
                                    if (body.topic == SupportTopic.payment) ...[
                                      const SizedBox(height: 12),
                                      SupportPaymentIssueFields(
                                        value: body.rentalContext.paymentIssue,
                                        onChanged: (value) => owner._body.value = body.copyWith(
                                          rentalContext: body.rentalContext.copyWith(paymentIssue: value),
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
''' +s[b:]
p.write_text(s)
