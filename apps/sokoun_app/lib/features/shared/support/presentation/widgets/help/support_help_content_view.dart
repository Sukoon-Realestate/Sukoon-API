part of '../../../imports.dart';

class SupportHelpContentView extends StatefulWidget {
  const SupportHelpContentView({super.key, required this.content});
  final SupportHelpContent content;
  @override
  State<SupportHelpContentView> createState() => _SupportHelpContentViewState();
}

class _SupportHelpContentViewState extends State<SupportHelpContentView> {
  final TextEditingController _search = TextEditingController();
  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _contact(Uri uri) async {
    bool opened = false;
    try {
      opened = await launchUrl(uri);
    } catch (_) {
      // A missing phone/mail app should leave the help center usable.
    }
    if (!opened && mounted) {
      Messages.showToast(
        msg: LocaleKeys.supportContactUnavailable,
        status: BaseStatus.error,
      );
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 24.h),
    shrinkWrap: true,
    primary: false,
    physics: const NeverScrollableScrollPhysics(),
    children: [
      if (widget.content.phone.isNotEmpty ||
          widget.content.email.isNotEmpty) ...[
        Card(
          child: Column(
            children: [
              if (widget.content.phone.isNotEmpty)
                ListTile(
                  leading: const Icon(Icons.phone_outlined),
                  title: AppText(
                    LocaleKeys.supportCallUs,
                    style: AppTextStyles.bold14,
                  ),
                  subtitle: Text(
                    widget.content.phone,
                    textDirection: TextDirection.ltr,
                  ),
                  onTap: () =>
                      _contact(Uri(scheme: 'tel', path: widget.content.phone)),
                ),
              if (widget.content.email.isNotEmpty)
                ListTile(
                  leading: const Icon(Icons.mail_outline),
                  title: AppText(
                    LocaleKeys.supportEmailUs,
                    style: AppTextStyles.bold14,
                  ),
                  subtitle: Text(
                    widget.content.email,
                    textDirection: TextDirection.ltr,
                  ),
                  onTap: () => _contact(
                    Uri(scheme: 'mailto', path: widget.content.email),
                  ),
                ),
              if (widget.content.hours.isNotEmpty)
                AppText(
                  widget.content.hours,
                  style: AppTextStyles.regular12.copyWith(
                    color: AppColors.sokoonGray,
                  ),
                ).paddingAll(12),
            ],
          ),
        ),
        16.szH,
      ],
      DefaultTextField(
        controller: _search,
        title: LocaleKeys.supportSearchHint,
        prefixIcon: const Icon(Icons.search_rounded),
        action: TextInputAction.search,
      ),
      16.szH,
      AppText(
        LocaleKeys.supportFaqTitle,
        style: AppTextStyles.bold16.copyWith(color: AppColors.sokoonNavy),
      ),
      12.szH,
      ValueListenableBuilder<TextEditingValue>(
        valueListenable: _search,
        builder: (context, value, _) {
          final String query = value.text.trim().toLowerCase();
          final List<SupportFaq> faqs = widget.content.faqs
              .where(
                (faq) => '${faq.question} ${faq.answer}'.toLowerCase().contains(
                  query,
                ),
              )
              .toList(growable: false);
          if (faqs.isEmpty) {
            return SupportFaqEmptyState(
              isSearching: query.isNotEmpty,
              onClear: _search.clear,
            );
          }
          return Column(
            spacing: 8.h,
            children: [
              for (final faq in faqs)
                SupportFaqTile(key: ValueKey(faq.id), faq: faq),
            ],
          );
        },
      ),
    ],
  );
}
