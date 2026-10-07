import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import '../../data/models/listing_suggestion.dart';

class ListingAiReview extends StatefulWidget {
  const ListingAiReview({
    super.key,
    required this.suggestion,
    required this.canApply,
  });
  final ListingSuggestion suggestion;
  final bool canApply;
  @override
  State<ListingAiReview> createState() => _ListingAiReviewState();
}

class _ListingAiReviewState extends State<ListingAiReview> {
  final GlobalKey<FormState> _form = GlobalKey<FormState>();
  late final TextEditingController _title;
  late final TextEditingController _description;
  @override
  void initState() {
    super.initState();
    _title = TextEditingController(text: widget.suggestion.suggestedTitle);
    _description = TextEditingController(
      text: widget.suggestion.suggestedDescription,
    );
  }

  @override
  void didUpdateWidget(ListingAiReview oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.suggestion.id != widget.suggestion.id) {
      _title.text = widget.suggestion.suggestedTitle;
      _description.text = widget.suggestion.suggestedDescription;
    }
  }

  @override
  void dispose() {
    _title.dispose();
    _description.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Form(
    key: _form,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(LocaleKeys.paidAiReview, fontWeight: FontWeight.bold),
        for (final warning in widget.suggestion.warnings) AppText(warning),
        16.szH,
        DefaultTextField(
          controller: _title,
          autovalidateMode: AutovalidateMode.disabled,
          maxLength: 150,
          decoration: InputDecoration(labelText: LocaleKeys.paidAiTitle),
          validator: (text) =>
              text?.trim().isNotEmpty == true ? null : LocaleKeys.fillField,
        ),
        16.szH,
        DefaultTextField(
          controller: _description,
          autovalidateMode: AutovalidateMode.disabled,
          inputType: TextInputType.multiline,
          action: TextInputAction.newline,
          maxLines: null,
          minLines: 4,
          maxLength: 5000,
          decoration: InputDecoration(labelText: LocaleKeys.paidAiDescription),
          validator: (text) =>
              text?.trim().isNotEmpty == true ? null : LocaleKeys.fillField,
        ),
        16.szH,
        AppText(LocaleKeys.paidAiEditNotice),
        if (widget.canApply)
          FilledButton(
            onPressed: () {
              if (_form.currentState!.validate()) {
                Go.back(
                  widget.suggestion.copyWith(
                    suggestedTitle: _title.text.trim(),
                    suggestedDescription: _description.text.trim(),
                  ),
                );
              }
            },
            child: AppText(LocaleKeys.paidAiApply),
          ),
        TextButton.icon(
          onPressed: () async {
            await Clipboard.setData(
              ClipboardData(text: '${_title.text}\n\n${_description.text}'),
            );
            Messages.showToast(msg: LocaleKeys.paidAiCopied);
          },
          icon: const Icon(Icons.copy_outlined),
          label: AppText(LocaleKeys.paidAiCopy),
        ),
      ],
    ),
  );
}
