part of '../../../imports.dart';

class SupportFaqTile extends StatefulWidget {
  const SupportFaqTile({super.key, required this.faq});
  final SupportFaq faq;
  @override
  State<SupportFaqTile> createState() => _SupportFaqTileState();
}

class _SupportFaqTileState extends State<SupportFaqTile> {
  final ValueNotifier<bool> _expanded = ValueNotifier(false);
  @override
  void dispose() {
    _expanded.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final duration = SokounMotion.duration(context);
    Widget answer(bool expanded) =>
        AppText(
              widget.faq.answer,
              style: AppTextStyles.regular14.copyWith(
                color: AppColors.sokoonGray,
                height: 1.6,
              ),
            )
            .paddingOnly(left: 16, right: 16, bottom: 16)
            .showIf(condition: () => expanded);
    return Card(
      margin: EdgeInsets.zero,
      color: AppColors.white,
      surfaceTintColor: AppColors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16.r),
        side: const BorderSide(color: AppColors.sokoonBorder),
      ),
      child: ValueListenableBuilder<bool>(
        valueListenable: _expanded,
        builder: (context, expanded, _) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Semantics(
              expanded: expanded,
              child: ListTile(
                title: AppText(
                  widget.faq.question,
                  style: AppTextStyles.bold14,
                ),
                trailing: Icon(
                  expanded ? Icons.expand_less : Icons.expand_more,
                  color: AppColors.sokoonTeal,
                ),
                onTap: () => _expanded.value = !expanded,
              ),
            ),
            duration == Duration.zero
                ? answer(expanded)
                : AnimatedSize(
                    duration: duration,
                    alignment: AlignmentDirectional.topStart,
                    child: answer(expanded),
                  ),
          ],
        ),
      ),
    );
  }
}
