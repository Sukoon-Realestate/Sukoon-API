import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../../data/models/owner_add_property_content.dart';
import '../../../data/models/property_upload_progress.dart';

class OwnerUploadProgressPanel extends StatelessWidget {
  const OwnerUploadProgressPanel({
    super.key,
    required this.uploads,
    required this.photos,
  });
  final Map<String, PropertyUploadProgress> uploads;
  final List<OwnerPropertyPhotoDraft> photos;

  String _label(PropertyUploadStatus status) => switch (status) {
    PropertyUploadStatus.queued => LocaleKeys.professionalUploadQueued,
    PropertyUploadStatus.sending => LocaleKeys.professionalUploadSending,
    PropertyUploadStatus.confirmed => LocaleKeys.professionalUploadConfirmed,
    PropertyUploadStatus.failed => LocaleKeys.professionalUploadFailed,
    PropertyUploadStatus.unknown => LocaleKeys.professionalUnknownOutcome,
  };

  @override
  Widget build(BuildContext context) {
    final int confirmed = uploads.values
        .where((item) => item.status == PropertyUploadStatus.confirmed)
        .length;
    return ExpansionTile(
      title: AppText(
        '${LocaleKeys.professionalUploadProgress} ($confirmed/${uploads.length})',
      ),
      children: [
        ConstrainedBox(
          constraints: const BoxConstraints(maxHeight: 160),
          child: ListView(
            shrinkWrap: true,
            children: [
              for (final entry in uploads.entries)
                ListTile(
                  dense: true,
                  title: AppText(
                    photos
                            .where((photo) => photo.reference == entry.key)
                            .firstOrNull
                            ?.name ??
                        LocaleKeys.ownerAddPropertyPhotosSummary,
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      AppText(_label(entry.value.status)),
                      if (entry.value.status == PropertyUploadStatus.sending)
                        LinearProgressIndicator(
                          value: entry.value.total > 0
                              ? (entry.value.sent / entry.value.total).clamp(
                                  0,
                                  1,
                                )
                              : null,
                        ),
                    ],
                  ),
                  trailing: entry.value.status == PropertyUploadStatus.confirmed
                      ? const Icon(Icons.check_circle_outline)
                      : null,
                ),
            ],
          ),
        ),
      ],
    );
  }
}
