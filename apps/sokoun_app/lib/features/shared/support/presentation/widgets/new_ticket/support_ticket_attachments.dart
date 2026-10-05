part of '../../../imports.dart';

class SupportTicketAttachments extends StatefulWidget {
  const SupportTicketAttachments({
    super.key,
    required this.files,
    required this.onChanged,
  });
  final List<File> files;
  final ValueChanged<List<File>> onChanged;
  @override
  State<SupportTicketAttachments> createState() =>
      _SupportTicketAttachmentsState();
}

class _SupportTicketAttachmentsState extends State<SupportTicketAttachments> {
  final ValueNotifier<bool> _picking = ValueNotifier(false);
  @override
  void dispose() {
    _picking.dispose();
    super.dispose();
  }

  Future<void> _pick() async {
    if (_picking.value || widget.files.length >= 3) return;
    _picking.value = true;
    try {
      final List<File> selected = await Helpers.getImages(limit: 3);
      final List<File> valid = [];
      for (final file in selected) {
        final String suffix = file.path.split('.').last.toLowerCase();
        if (!['jpg', 'jpeg', 'png', 'webp'].contains(suffix) ||
            await file.length() > 5 * 1024 * 1024) {
          if (mounted) {
            Messages.showToast(
              msg: LocaleKeys.supportAttachmentLimit,
              status: BaseStatus.error,
            );
          }
          continue;
        }
        valid.add(file);
      }
      if (mounted) {
        widget.onChanged([...widget.files, ...valid].take(3).toList());
      }
    } catch (_) {
      if (mounted) {
        Messages.showToast(
          msg: LocaleKeys.supportAttachmentUnavailable,
          status: BaseStatus.error,
        );
      }
    } finally {
      if (mounted) _picking.value = false;
    }
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 8.h,
    children: [
      AppText(LocaleKeys.supportAttachments, style: AppTextStyles.bold14),
      AppText(
        LocaleKeys.supportAttachmentLimit,
        style: AppTextStyles.regular12.copyWith(
          color: AppColors.sokoonGray,
          height: 1.5,
        ),
      ),
      for (final file in widget.files)
        ListTile(
          leading: const Icon(Icons.image_outlined),
          title: AppText(
            file.path.split('/').last,
            style: AppTextStyles.regular14,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          trailing: IconButton(
            tooltip: LocaleKeys.supportRemoveAttachment,
            icon: const Icon(Icons.close_rounded),
            onPressed: () => widget.onChanged(
              widget.files.where((item) => item != file).toList(),
            ),
          ),
        ),
      ValueListenableBuilder<bool>(
        valueListenable: _picking,
        builder: (context, picking, _) => OutlinedButton.icon(
          onPressed: picking || widget.files.length >= 3 ? null : _pick,
          icon: const Icon(Icons.add_photo_alternate_outlined),
          label: AppText(
            picking
                ? LocaleKeys.supportPickingImages
                : LocaleKeys.supportAddImages,
            style: AppTextStyles.bold14,
          ),
        ),
      ),
    ],
  );
}
