import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../../data/models/owner_add_property_content.dart';
import '../../../data/models/owner_property_draft.dart';
import '../../../data/models/property_upload_progress.dart';
import '../../cubits/owner_draft_cubit.dart';
import 'owner_draft_save_warning.dart';
import 'owner_upload_progress_panel.dart';

class OwnerDraftStatus extends StatelessWidget {
  const OwnerDraftStatus({
    super.key,
    required this.cubit,
    required this.form,
    required this.retry,
    this.uploadProgress,
  });
  final OwnerDraftCubit cubit;
  final ValueListenable<OwnerAddPropertyFormState> form;
  final Future<void> Function() retry;
  final Stream<Map<String, PropertyUploadProgress>>? uploadProgress;

  @override
  Widget build(
    BuildContext context,
  ) => BlocBuilder<OwnerDraftCubit, OwnerPropertyDraft>(
    bloc: cubit,
    builder: (context, draft) =>
        ValueListenableBuilder<OwnerAddPropertyFormState>(
          valueListenable: form,
          builder: (context, current, _) => ConstrainedBox(
            constraints: BoxConstraints(
              maxHeight: MediaQuery.sizeOf(context).height * 0.22,
            ),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (!draft.localSaveFailed &&
                      (draft.isSaving || draft.savedAt != null))
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: Semantics(
                        liveRegion: true,
                        child: AppText(
                          draft.isSaving
                              ? LocaleKeys.professionalSaving
                              : LocaleKeys.freeDraftSaved,
                        ),
                      ),
                    ),
                  if (draft.unknownMutation ||
                      draft.uploads.values.any(
                        (item) => item.status == PropertyUploadStatus.unknown,
                      ))
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: Semantics(
                        liveRegion: true,
                        child: AppText(LocaleKeys.professionalUnknownOutcome),
                      ),
                    ),
                  if (draft.localSaveFailed)
                    OwnerDraftSaveWarning(onRetry: retry),
                  if (draft.needsPrivateDocument &&
                      current.ownershipProofFile == null)
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: AppText(LocaleKeys.professionalReselectDocument),
                    ),
                  if (draft.hasMissingFiles ||
                      current.photoDrafts.any(
                        (photo) => photo.needsReselection,
                      ))
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: AppText(LocaleKeys.freeDraftMissingFiles),
                    ),
                  if (!current.canSaveToServer())
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: AppText(LocaleKeys.rentalLocalOnly),
                    ),
                  if (draft.uploads.isNotEmpty)
                    StreamBuilder<Map<String, PropertyUploadProgress>>(
                      stream: uploadProgress,
                      initialData: draft.uploads,
                      builder: (context, snapshot) => OwnerUploadProgressPanel(
                        uploads: snapshot.data ?? draft.uploads,
                        photos: current.photoDrafts,
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
  );
}
