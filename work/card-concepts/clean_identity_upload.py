from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
base=root/'apps/sokoun_app/lib/features/shared/auth/presentation/widgets/kyc'
p=base/'identity_capture_guidance.dart'
p.write_text('''import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';

class IdentityCaptureGuidance extends StatelessWidget {
  const IdentityCaptureGuidance({super.key});
  @override
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: palette.raised,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ExcludeSemantics(child: Icon(Icons.crop_free_rounded, size: 20, color: palette.accent)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppText(LocaleKeys.uxIdentityCaptureGuidance,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.text, height: 1.5)),
                const SizedBox(height: 6),
                AppText(LocaleKeys.uxIdentityLocalAdvice,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.muted, height: 1.5)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
''')
p=base/'identity_document_summary.dart'
s=p.read_text().replace("import 'package:flutter/material.dart';", "import 'package:flutter/material.dart';\nimport 'package:sokoun_app/shared_widgets/sokoun_palette.dart';")
a=s.index('  @override\n  Widget build')
s=s[:a]+'''  @override
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    final status = switch (document.status) {
      IdentityDocumentStatus.approved => LocaleKeys.uxIdentityAccepted,
      IdentityDocumentStatus.pending => LocaleKeys.uxIdentityPending,
      IdentityDocumentStatus.rejected => LocaleKeys.uxIdentityCorrectionNeeded,
      IdentityDocumentStatus.missing => LocaleKeys.uxIdentityNotProvided,
      IdentityDocumentStatus.unknown => LocaleKeys.uxIdentityUnknown,
    };
    final color = switch (document.status) {
      IdentityDocumentStatus.approved => palette.success,
      IdentityDocumentStatus.rejected => palette.error,
      IdentityDocumentStatus.pending => palette.warning,
      _ => palette.muted,
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Wrap(
          alignment: WrapAlignment.spaceBetween,
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 8,
          runSpacing: 4,
          children: [
            AppText(identityDocumentTitle(document.kind),
              style: Theme.of(context).textTheme.titleSmall?.copyWith(color: palette.text, height: 1.5)),
            AppText(status,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: color, height: 1.5)),
          ],
        ),
        if (document.reason.isNotEmpty) ...[
          const SizedBox(height: 6),
          AppText(document.reason,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.error, height: 1.5)),
        ],
      ],
    );
  }
}
'''
p.write_text(s)
p=base/'kyc_upload_tile.dart'
s=p.read_text().replace("import 'dart:io';", "import 'dart:io';\nimport 'package:sokoun_app/shared_widgets/sokoun_palette.dart';")
s=s.replace('    this.emptySubtitle,', '    this.emptySubtitle,\n    this.compact = false,')
s=s.replace('  final String title;', '  final String title;\n  final bool compact;', 1)
s=s.replace('''  Widget build(BuildContext context) {
    final borderColor''', '''  Widget build(BuildContext context) {
    if (compact) return _CompactUploadTile(tile: this);
    final borderColor''', 1)
s+='''
class _CompactUploadTile extends StatelessWidget {
  const _CompactUploadTile({required this.tile});
  final KycUploadTile tile;

  @override
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    final image = tile.image;
    final selected = tile._isUploaded;
    final label = selected
        ? tile.fileName ?? image?.path.split('/').last ?? LocaleKeys.uploaded
        : tile.emptyTitle ?? LocaleKeys.tapToUpload;
    return Semantics(
      label: tile.title,
      child: Material(
        color: palette.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: selected ? palette.accent : palette.line),
        ),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: tile.onTap,
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                if (image != null)
                  ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: Image.file(image, width: 40, height: 40, fit: BoxFit.cover),
                  )
                else
                  ExcludeSemantics(child: Icon(
                    selected ? Icons.check_circle_outline_rounded : tile.emptyIcon,
                    color: tile.onTap == null ? palette.muted : palette.accent,
                    size: 24,
                  )),
                const SizedBox(width: 12),
                Expanded(child: AppText(label,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: tile.onTap == null ? palette.muted : palette.text, height: 1.5),
                  maxLines: selected ? 2 : null,
                  overflow: selected ? TextOverflow.ellipsis : null,
                )),
                const SizedBox(width: 8),
                ExcludeSemantics(child: Icon(selected ? Icons.edit_outlined : Icons.add_rounded,
                  size: 20, color: palette.muted)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
'''
p.write_text(s)
p=base/'identity_correction_form.dart'
s=p.read_text().replace("import 'package:flutter/material.dart';", "import 'package:flutter/material.dart';\nimport 'package:sokoun_app/shared_widgets/sokoun_palette.dart';")
s=s.replace('''            KycUploadTile(
              title:''', '''            KycUploadTile(
              compact: true,
              emptyIcon: doc.kind == IdentityDocumentKind.selfie
                  ? Icons.add_a_photo_outlined : Icons.upload_file_outlined,
              emptyTitle: doc.kind == IdentityDocumentKind.selfie
                  ? LocaleKeys.capturePhoto : null,
              title:''')
s=s.replace('''        if (!data.hasPendingOperation &&''', '''        if (data.preparation.documents.any((doc) => doc.canReplace &&
            doc.kind != IdentityDocumentKind.nationalId && doc.kind != IdentityDocumentKind.unknown)) ...[
          AppText(MediaValidators.accountDocumentUploadHint,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: SokounPalette.of(context).muted, height: 1.5)),
          const SizedBox(height: 16),
        ],
        if (!data.hasPendingOperation &&''',1)
p.write_text(s)
