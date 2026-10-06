part of '../../../imports.dart';

class VisitCalendarButton extends StatelessWidget {
  const VisitCalendarButton({super.key, required this.visit});
  final TenantVisitContent visit;
  @override
  Widget build(BuildContext context) {
    if (VisitCalendarData.build(visit) == null) return const SizedBox.shrink();
    return AppLoadingButton(
      title: LocaleKeys.freeExportVisitCalendar,
      asyncCall: (_) async {
        final box = context.findRenderObject();
        if (box is! RenderBox || !box.hasSize) return;
        try {
          await VisitCalendarData.share(
            visit,
            origin: box.localToGlobal(Offset.zero) & box.size,
          );
        } catch (_) {
          Messages.showToast(msg: LocaleKeys.freeCalendarExportFailed);
        }
      },
    );
  }
}
