import '../widgets/owner_add_property/owner_draft_status.dart';
import '../../data/owner_draft_reconcile_data.dart';
import '../../data/models/property_upload_progress.dart';
import '../cubits/owner_draft_review_cubit.dart';
import '../widgets/owner_add_property/owner_draft_conflict_dialog.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../data/owner_accommodation_draft_data.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_draft_editing.dart';
import '../widgets/owner_add_property/rental_scope_selector.dart';
import 'package:sokoun_app/features/owner/ai_assistant/presentation/widgets/listing_ai_entry.dart';
import 'dart:async';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import '../../data/owner_draft_data.dart';
import '../../data/models/owner_property_draft.dart';
import '../../data/enums/owner_draft_action.dart';
import '../cubits/owner_draft_cubit.dart';
import '../cubits/owner_property_photos_cubit.dart';
import '../widgets/owner_add_property/owner_draft_dialog.dart';
import '../../data/models/property_location.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/shared_widgets/unsaved_changes_guard.dart';

import '../../data/owner_add_property_mapper.dart';
import '../../data/enums/property_review_action.dart';
import '../widgets/owner_add_property/property_review_sheet.dart';
import '../widgets/owner_add_property/property_edit_review_sheet.dart';
import '../../data/models/owner_add_property_content.dart';
import '../cubits/property_submission_cubit.dart';
import '../cubits/upload_property_images_cubit.dart';
import '../widgets/owner_add_property/imports.dart';

class OwnerPropertyFlowScreen extends StatefulWidget {
  const OwnerPropertyFlowScreen({super.key, this.property, this.offerId});

  final PropertyDetailsModel? property;
  final String? offerId;

  @override
  State<OwnerPropertyFlowScreen> createState() =>
      _OwnerPropertyFlowScreenState();
}

class _OwnerPropertyFlowScreenState extends State<OwnerPropertyFlowScreen>
    with WidgetsBindingObserver {
  late final PageController _pageController;
  late final OwnerDraftCubit _draftCubit;
  late Future<void> _draftRequest;
  bool _restoringDraft = false;
  bool _needsRevalidation = false;
  bool _unknownMutation = false;
  bool _resumeUploadsOnly = false;
  String _baseRevision = '';
  OwnerAddPropertyFormState? _baseForm;
  Map<String, PropertyUploadProgress> _uploads = {};
  Set<String>? _restoredDirtyFields;
  OwnerDraftReviewCubit? _reviewCubit;
  final ValueNotifier<int> _currentStep = ValueNotifier(0);
  PropertySubmissionCubit? _submissionCubit;
  OwnerPropertyPhotosCubit? _photosCubit;
  UploadPropertyImagesCubit? _uploadPropertyImagesCubit;
  PropertyDetailsModel? _savedProperty;
  OwnerAddPropertyFormState? _savedForm;
  String _submissionMessage = '';
  late final ValueNotifier<OwnerAddPropertyFormState> _formNotifier;
  OwnerPropertyLocationModel? _selectedGovernorate;
  OwnerPropertyLocationModel? _selectedCity;
  int _locationDropdownGeneration = 0;
  final ValueNotifier<bool> _isSubmitting = ValueNotifier<bool>(false);
  bool _hasChanges = false;
  bool _isReviewOpen = false;

  late final TextEditingController _titleController;
  late final TextEditingController _streetController;
  late final TextEditingController _bedroomsController;
  late final TextEditingController _bathroomsController;
  late final TextEditingController _spaceController;
  late final TextEditingController _floorController;
  late final TextEditingController _monthlyPriceController;
  late final TextEditingController _rentalDurationController;
  late final TextEditingController _descriptionController;

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    final PropertyDetailsModel? property = widget.property;
    final OwnerPropertyFormSeed? seed = property == null
        ? null
        : OwnerAddPropertyMapper.fromProperty(
            property,
            offerId: widget.offerId,
          );
    _formNotifier = ValueNotifier<OwnerAddPropertyFormState>(
      (seed?.form ?? OwnerAddPropertyFormState.initial()).copyWith(
        submissionKey: RentalDraftEditing.key(),
      ),
    );
    _baseForm = seed?.form;
    _baseRevision = property?.updatedAt ?? '';
    _selectedGovernorate = seed?.governorate;
    _selectedCity = seed?.city;
    _titleController = TextEditingController(text: _form.title);
    _streetController = TextEditingController(text: _form.street);
    _bedroomsController = TextEditingController(text: _form.bedrooms);
    _bathroomsController = TextEditingController(text: _form.bathrooms);
    _spaceController = TextEditingController(text: _form.space);
    _floorController = TextEditingController(text: _form.floor);
    _monthlyPriceController = TextEditingController(text: _form.monthlyPrice);
    _rentalDurationController = TextEditingController(
      text: _form.rentalDuration,
    );
    _descriptionController = TextEditingController(text: _form.description);
    WidgetsBinding.instance.addObserver(this);
    _draftCubit = OwnerDraftCubit(
      store: OwnerDraftData(
        accountId: UserModel.currentUser?.id ?? '',
        propertyId: widget.property?.id ?? '',
      ),
    );
    _formNotifier.addListener(_scheduleDraft);
    _draftRequest = _restoreDraft();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _formNotifier.removeListener(_scheduleDraft);
    unawaited(_draftCubit.close().catchError((Object _) {}));
    _pageController.dispose();
    _currentStep.dispose();
    _formNotifier.dispose();
    _isSubmitting.dispose();
    _submissionCubit?.close();
    _photosCubit?.close();
    _reviewCubit?.close();
    _uploadPropertyImagesCubit?.close();
    _titleController.dispose();
    _streetController.dispose();
    _bedroomsController.dispose();
    _bathroomsController.dispose();
    _spaceController.dispose();
    _floorController.dispose();
    _monthlyPriceController.dispose();
    _rentalDurationController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  OwnerPropertyDraft get _draft => OwnerPropertyDraft(
    form: _form,
    savedProperty: _savedProperty,
    isServerSnapshotCurrent: identical(_savedForm, _form),
    serverFormConfirmed: identical(_savedForm, _form) || _resumeUploadsOnly,
    step: _currentStep.value.clamp(0, 2),
    baseRevision: _baseRevision,
    dirtyFields:
        _restoredDirtyFields ??
        OwnerDraftReconcileData.dirtyFields(_form, _baseForm),
    unknownMutation: _unknownMutation,
    needsPrivateDocument: _draftCubit.state.needsPrivateDocument,
    uploads: _uploads,
  );

  void _scheduleDraft() {
    if (!_restoringDraft && _hasChanges && _form.submittedAt == null) {
      _resumeUploadsOnly = false;
      if (_restoredDirtyFields != null) {
        _restoredDirtyFields = {
          ..._restoredDirtyFields!,
          ...OwnerDraftReconcileData.dirtyFields(_form, _baseForm),
        };
      }
      _draftCubit.schedule(_draft);
    }
  }

  Future<void> _persistDraft() => _draftCubit.save(_draft);

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) {
      unawaited(_draftCubit.flush().catchError((Object _) {}));
    }
  }

  Future<void> _restoreDraft() async {
    await _draftCubit.load();
    if (!mounted || _draftCubit.state.form == null) return;
    await WidgetsBinding.instance.endOfFrame;
    if (!mounted) return;
    final action = await showDialog<OwnerDraftAction>(
      context: context,
      barrierDismissible: false,
      builder: (_) => const OwnerDraftDialog(isRecovery: true),
    );
    if (!mounted) return;
    if (action == OwnerDraftAction.discard) {
      await _draftCubit.clear();
      return;
    }
    final draft = _draftCubit.state;
    final form = draft.form;
    if (form == null) return;
    _restoringDraft = true;
    _savedProperty = draft.savedProperty;
    _savedForm = null;
    _needsRevalidation = (draft.savedProperty ?? widget.property) != null;
    _baseRevision = draft.baseRevision;
    _restoredDirtyFields = draft.dirtyFields;
    _unknownMutation = draft.unknownMutation;
    _uploads = draft.uploads;
    _resumeUploadsOnly = draft.serverFormConfirmed;
    _baseForm = form;
    _selectedGovernorate = form.governorateId.isEmpty
        ? null
        : const OwnerPropertyLocationModel.initial().copyWith(
            id: form.governorateId,
            name: form.governorate,
          );
    _selectedCity = form.districtId.isEmpty
        ? null
        : const OwnerPropertyLocationModel.initial().copyWith(
            id: form.districtId,
            name: form.district,
          );
    _locationDropdownGeneration++;
    _formNotifier.value = form;
    _syncControllers();
    _hasChanges = true;
    _restoringDraft = false;
    if (draft.hasMissingFiles) {
      Messages.showToast(msg: LocaleKeys.freeDraftMissingFiles);
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _goToPage(draft.step);
    });
  }

  Future<bool> _confirmLeave() async {
    final action = await showDialog<OwnerDraftAction>(
      context: context,
      builder: (_) => const OwnerDraftDialog(isRecovery: false),
    );
    if (action == null || action == OwnerDraftAction.stay) return false;
    try {
      if (action == OwnerDraftAction.discard) {
        await _draftCubit.clear();
      } else {
        await _persistDraft();
      }
      _hasChanges = false;
      return true;
    } catch (_) {
      Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
      return false;
    }
  }

  bool get _isEditing => widget.property != null;

  OwnerAddPropertyFormState get _form => _formNotifier.value;

  void _updateForm(OwnerAddPropertyFormState Function() update) {
    if (_isSubmitting.value) return;
    _hasChanges = true;
    _formNotifier.value = update();
    _syncControllers();
  }

  void _goToPage(int page) {
    // Programmatic step changes can leave the previous page's input focused.
    FocusManager.instance.primaryFocus?.unfocus();
    if (!_pageController.hasClients) return;
    final duration = SokounMotion.duration(context, milliseconds: 280);
    if (duration == Duration.zero) {
      _pageController.jumpToPage(page);
    } else {
      _pageController.animateToPage(
        page,
        duration: duration,
        curve: SokounMotion.curve,
      );
    }
  }

  Future<void> _reviewAndSubmit() async {
    if (_isReviewOpen ||
        _isSubmitting.value ||
        !_form.isBasicsReady ||
        !_form.isPhotosReady ||
        !_form.isPricingReady) {
      return;
    }
    _isReviewOpen = true;
    try {
      _isSubmitting.value = true;
      final checked = await (_photosCubit ??= OwnerPropertyPhotosCubit()).check(
        _form.photoDrafts,
      );
      if (!mounted) return;
      _isSubmitting.value = false;
      if (checked == null) return;
      if (checked.photos.indexed.any(
        (entry) => !identical(entry.$2, _form.photoDrafts[entry.$1]),
      )) {
        _updateForm(() => _form.copyWith(photoDrafts: checked.photos));
      }
      if (checked.hasDuplicates) {
        Messages.showToast(
          msg: LocaleKeys.rentalDuplicatePhotos,
          status: BaseStatus.error,
        );
        _goToPage(1);
        return;
      }
      final action = await showModalBottomSheet<PropertyReviewAction>(
        context: context,
        isScrollControlled: true,
        useSafeArea: true,
        showDragHandle: true,
        backgroundColor: context.appColor(AppColors.white, surface: true),
        sheetAnimationStyle: AnimationStyle(
          duration: SokounMotion.duration(context, milliseconds: 280),
          reverseDuration: SokounMotion.duration(context, milliseconds: 220),
        ),
        constraints: BoxConstraints(
          maxWidth: 640,
          maxHeight: MediaQuery.sizeOf(context).height * .9,
        ),
        builder: (_) => PropertyReviewSheet(form: _form, isEditing: _isEditing),
      );
      if (!mounted || action == null) return;
      if (action == PropertyReviewAction.submit) {
        await _submitForReview();
      } else {
        _goToPage(action.page!);
      }
    } finally {
      _isReviewOpen = false;
      if (mounted) _isSubmitting.value = false;
    }
  }

  void _syncControllers() {
    for (final entry in {
      _titleController: _form.title,
      _streetController: _form.street,
      _bedroomsController: _form.bedrooms,
      _bathroomsController: _form.bathrooms,
      _spaceController: _form.space,
      _floorController: _form.floor,
      _monthlyPriceController: _form.monthlyPrice,
      _rentalDurationController: _form.rentalDuration,
      _descriptionController: _form.description,
    }.entries) {
      if (entry.key.text != entry.value) entry.key.text = entry.value;
    }
  }

  void _resetFlow() {
    _hasChanges = false;
    _savedProperty = null;
    _submissionMessage = '';
    _savedForm = null;
    _baseForm = null;
    _baseRevision = '';
    _restoredDirtyFields = null;
    _resumeUploadsOnly = false;
    _unknownMutation = false;
    _uploads = {};
    _needsRevalidation = false;
    _selectedGovernorate = null;
    _selectedCity = null;
    _locationDropdownGeneration++;
    _formNotifier.value = OwnerAddPropertyFormState.initial().copyWith(
      submissionKey: RentalDraftEditing.key(),
    );
    _syncControllers();
    if (_pageController.hasClients) {
      _pageController.jumpToPage(0);
    }
  }

  void _selectGovernorate(OwnerPropertyLocationModel governorate) {
    if (_selectedGovernorate == governorate) {
      return;
    }
    _selectedGovernorate = governorate;
    _selectedCity = null;
    _updateForm(
      () => _form.copyWith(
        governorateId: governorate.id,
        governorate: governorate.name,
        districtId: '',
        district: '',
        clearLocation: true,
      ),
    );
  }

  void _selectCity(OwnerPropertyLocationModel city) {
    if (_selectedCity == city) {
      return;
    }
    _selectedCity = city;
    _updateForm(
      () => _form.copyWith(
        districtId: city.id,
        district: city.name,
        clearLocation: true,
      ),
    );
  }

  void _selectLocation(PropertyLocation location) {
    _updateForm(() => _form.copyWith(location: location));
  }

  Future<void> _addPhotos() async {
    if (_isSubmitting.value ||
        _form.photoCount >= OwnerAddPropertyContent.maxPhotoCount) {
      return;
    }
    final int remaining =
        OwnerAddPropertyContent.maxPhotoCount - _form.photoCount;
    final List<File> selectedPhotos = await Helpers.getImages(limit: remaining);
    if (!mounted || _isSubmitting.value || selectedPhotos.isEmpty) {
      return;
    }
    final List<OwnerPropertyPhotoDraft> photoDrafts = [
      ..._form.photoDrafts,
      ...selectedPhotos
          .take(remaining)
          .map(
            (photo) => OwnerPropertyPhotoDraft(
              file: photo,
              draftKey: RentalDraftEditing.key(),
            ),
          ),
    ];
    _updateForm(() => _form.copyWith(photoDrafts: photoDrafts));
  }

  void _removePhoto(int index) {
    if (index < 0 || index >= _form.photoCount) {
      return;
    }
    if (!_form.photoDrafts[index].canRemove) return;
    final removed = _form.photoDrafts[index];
    final status = _uploads[removed.reference]?.status;
    if (status == PropertyUploadStatus.sending ||
        status == PropertyUploadStatus.unknown) {
      Messages.showToast(msg: LocaleKeys.professionalUnknownOutcome);
      return;
    }
    final removedId = removed.existingId;
    final previousInventory = _form.rentalInventory;
    final List<OwnerPropertyPhotoDraft> photoDrafts =
        List<OwnerPropertyPhotoDraft>.of(_form.photoDrafts)..removeAt(index);
    _updateForm(
      () => _form.copyWith(
        photoDrafts: photoDrafts,
        rentalInventory: RentalDraftEditing.withoutMedia(
          RentalDraftEditing.withoutMedia(
            _form.rentalInventory,
            removed.reference,
          ),
          removedId,
        ),
      ),
    );
    final remainingInventory = _form.rentalInventory;
    if (!removed.isExisting &&
        (_uploads[removed.reference]?.status ?? PropertyUploadStatus.queued) !=
            PropertyUploadStatus.unknown) {
      Messages.showToast(
        msg: LocaleKeys.professionalPhotoRemoved,
        actionLabel: LocaleKeys.favoritesUndoAction,
        onAction: () {
          if (!mounted ||
              _isSubmitting.value ||
              _form.photoDrafts.length >= 25 ||
              _form.photoDrafts.any(
                (photo) => photo.reference == removed.reference,
              )) {
            return;
          }
          final photos = List<OwnerPropertyPhotoDraft>.of(_form.photoDrafts)
            ..insert(index.clamp(0, _form.photoCount), removed);
          _updateForm(
            () => _form.copyWith(
              photoDrafts: photos,
              rentalInventory:
                  identical(_form.rentalInventory, remainingInventory)
                  ? previousInventory
                  : _form.rentalInventory,
            ),
          );
        },
      );
    }
  }

  Future<void> _replacePhoto(int index) async {
    if (_isSubmitting.value || index < 0 || index >= _form.photoCount) return;
    final OwnerPropertyPhotoDraft current = _form.photoDrafts[index];
    final File? replacement = await Helpers.getImage();
    if (!mounted ||
        _isSubmitting.value ||
        replacement == null ||
        index >= _form.photoCount ||
        _form.photoDrafts[index] != current) {
      return;
    }
    final List<OwnerPropertyPhotoDraft> photoDrafts =
        List<OwnerPropertyPhotoDraft>.of(_form.photoDrafts);
    photoDrafts[index] = current.copyWith(
      file: replacement,
      existingId: '',
      existingUrl: '',
      contentFingerprint: '',
      draftKey: RentalDraftEditing.key(),
      needsReselection: false,
    );
    _updateForm(
      () => _form.copyWith(
        photoDrafts: photoDrafts,
        rentalInventory: RentalDraftEditing.withoutMedia(
          _form.rentalInventory,
          current.existingId,
        ),
      ),
    );
  }

  void _movePhoto(({int from, int to}) move) {
    if (move.from < 0 ||
        move.to < 0 ||
        move.from >= _form.photoCount ||
        move.to >= _form.photoCount) {
      return;
    }
    final photos = List<OwnerPropertyPhotoDraft>.of(_form.photoDrafts);
    photos.insert(move.to, photos.removeAt(move.from));
    _updateForm(() => _form.copyWith(photoDrafts: photos));
  }

  void _selectMainPhoto(int index) {
    if (index <= 0 || index >= _form.photoCount) return;
    final List<OwnerPropertyPhotoDraft> photos = List.of(_form.photoDrafts);
    photos.insert(0, photos.removeAt(index));
    _updateForm(() => _form.copyWith(photoDrafts: photos));
  }

  void _updatePhotoMetadata({
    required int index,
    String? name,
    String? description,
  }) {
    if (index < 0 || index >= _form.photoCount) return;
    final List<OwnerPropertyPhotoDraft> photoDrafts =
        List<OwnerPropertyPhotoDraft>.of(_form.photoDrafts);
    photoDrafts[index] = photoDrafts[index].copyWith(
      name: name,
      description: description,
    );
    _updateForm(() => _form.copyWith(photoDrafts: photoDrafts));
  }

  void _toggleAmenity(String amenity) {
    final amenities = Set<String>.from(_form.amenityApiValues);
    if (amenities.contains(amenity)) {
      amenities.remove(amenity);
    } else {
      amenities.add(amenity);
    }
    _updateForm(() => _form.copyWith(amenities: amenities));
  }

  Future<void> _submitForReview() async {
    if (_isSubmitting.value) return;
    if (!_form.canSaveToServer()) {
      _isSubmitting.value = true;
      try {
        await _persistDraft();
        if (mounted) Messages.showToast(msg: LocaleKeys.rentalDraftSaved);
      } catch (_) {
        if (mounted) {
          Messages.showToast(
            msg: LocaleKeys.freeLocalSaveFailed,
            status: BaseStatus.error,
          );
        }
      } finally {
        if (mounted) _isSubmitting.value = false;
      }
      return;
    }
    if (_isSubmitting.value ||
        !_form.isBasicsReady ||
        !_form.isPhotosReady ||
        !_form.isPricingReady) {
      return;
    }
    _isSubmitting.value = true;
    bool wasSubmitted = false;
    try {
      if (!await _saveProperty() || !mounted) return;
      final PropertyDetailsModel? property = _savedProperty;
      if (property == null) return;
      final UploadPropertyImagesCubit cubit = _uploadPropertyImagesCubit ??=
          UploadPropertyImagesCubit();
      await cubit.uploadImages(
        propertyId: property.id,
        photos: _form.photoDrafts,
        restoredUploads: _uploads,
        onProgressChanged: (uploads) async {
          _uploads = uploads;
          await _persistDraft();
        },
        onPhotoUploaded: _recordUploadedPhoto,
        onSuccess: () {
          wasSubmitted = true;
          if (_submissionMessage.isEmpty) {
            _submissionMessage = cubit.state.msg ?? '';
          }
        },
      );
    } catch (_) {
      if (mounted) Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
    } finally {
      if (mounted) _isSubmitting.value = false;
    }
    if (!mounted || !wasSubmitted) return;
    try {
      await _draftCubit.clear();
    } catch (_) {
      Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
    }
    if (!mounted) return;
    _hasChanges = false;
    if (_submissionMessage.isNotEmpty) {
      Messages.showToast(msg: _submissionMessage);
    }
    if (_isEditing) {
      await showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        useSafeArea: true,
        showDragHandle: true,
        builder: (_) => PropertyEditReviewSheet(message: _submissionMessage),
      );
      if (!mounted) return;
      Go.back(_savedProperty);
    } else {
      _formNotifier.value = _form.copyWith(submittedAt: DateTime.now());
      _goToPage(3);
    }
  }

  Future<bool> _saveProperty() async {
    if (_form.submissionKey.isEmpty) {
      _formNotifier.value = _form.copyWith(
        submissionKey: RentalDraftEditing.key(),
      );
    }
    if (_unknownMutation) {
      Messages.showToast(
        msg: LocaleKeys.professionalUnknownOutcome,
        status: BaseStatus.error,
      );
      return false;
    }
    final PropertyDetailsModel? previous = _savedProperty ?? widget.property;
    if (_needsRevalidation && previous != null) {
      final fresh = await (_reviewCubit ??= OwnerDraftReviewCubit()).fresh(
        previous.id,
      );
      if (!mounted || fresh == null) return false;
      final bool changed = _resumeUploadsOnly
          ? !OwnerDraftReconcileData.matchesAcknowledged(previous, fresh)
          : _baseRevision.isEmpty ||
                fresh.updatedAt.isEmpty ||
                fresh.updatedAt != _baseRevision;
      if (changed) {
        final reviewed = await showDialog<bool>(
          context: context,
          builder: (_) => OwnerDraftConflictDialog(
            currentTitle: fresh.title,
            draftTitle: _form.title,
          ),
        );
        if (!mounted || reviewed != true) return false;
        _formNotifier.value = OwnerDraftReconcileData.merge(
          draft: _form,
          fresh: fresh,
          dirtyFields:
              _restoredDirtyFields ??
              OwnerDraftReconcileData.dirtyFields(_form, _baseForm),
        );
        _syncControllers();
        _goToPage(0);
      }
      _savedProperty = fresh;
      _baseRevision = fresh.updatedAt;
      _baseForm = OwnerAddPropertyMapper.fromProperty(fresh).form;
      _needsRevalidation = false;
      if (!changed && _resumeUploadsOnly) _savedForm = _form;
      await _persistDraft();
      if (changed) {
        return false; // Review the form again before explicit submission.
      }
    }
    await _persistDraft();
    final OwnerAddPropertyFormState form = _form;
    if (identical(_savedForm, form)) return true;
    final PropertyDetailsModel? property = _savedProperty ?? widget.property;
    bool wasSaved = false;
    Future<void>? coverSave;
    final PropertySubmissionCubit cubit = _submissionCubit ??=
        PropertySubmissionCubit();
    _unknownMutation = true;
    await _persistDraft();
    await cubit.save(
      propertyId: property?.id,
      form: form,
      onSuccess: (response) {
        if (!mounted) return;
        _unknownMutation = false;
        _savedProperty = response;
        _baseRevision = response.updatedAt;
        if (response.rentalInventory != null) {
          _formNotifier.value = _form.copyWith(
            rentalInventory: response.rentalInventory,
          );
        }
        _submissionMessage = cubit.state.msg ?? '';
        final OwnerPropertyPhotoDraft? mainPhoto = form.photoDrafts.firstOrNull;
        if (mainPhoto?.file != null && response.mainImage.isNotEmpty) {
          final PropertyImageModel main = response.images.firstWhere(
            (image) => image.image == response.mainImage,
            orElse: () => PropertyImageModel.initial().copyWith(
              id: response.mainImageId,
              image: response.mainImage,
              name: response.mainImageName,
              description: response.mainImageDescription,
            ),
          );
          coverSave = _recordUploadedPhoto(photo: mainPhoto!, image: main);
        }
        if (form.videoFile != null && response.video?.isNotEmpty == true) {
          _formNotifier.value = _form
              .copyWith(clearVideo: true)
              .copyWith(
                videoUrl: response.video,
                videoDuration: response.videoDuration,
              );
        }
        if (form.ownershipProofFile != null &&
            response.ownershipProof.isNotEmpty) {
          _formNotifier.value = _form
              .copyWith(clearOwnershipProof: true)
              .copyWith(ownershipProofUrl: response.ownershipProof);
        }
        wasSaved = true;
      },
    );
    if (!wasSaved && !cubit.outcomeUnknown) {
      _unknownMutation = false;
      await _persistDraft();
    }
    if (!wasSaved && cubit.outcomeUnknown && cubit.recoveryProperty == null) {
      _unknownMutation = true;
      await _persistDraft();
      if (mounted) {
        Messages.showToast(
          msg: LocaleKeys.professionalUnknownOutcome,
          status: BaseStatus.error,
        );
      }
    }
    if (!wasSaved && cubit.recoveryProperty != null) {
      _savedProperty = cubit.recoveryProperty;
      await _persistDraft();
      if (mounted) {
        Messages.showToast(
          msg: cubit.state.msg ?? LocaleKeys.rentalIncompatibleResponse,
          status: BaseStatus.error,
        );
      }
    }
    if (wasSaved) {
      await coverSave;
      _savedForm = _form;
      _baseForm = _form;
      _restoredDirtyFields = {};
      await _persistDraft();
    }
    return wasSaved;
  }

  Future<void> _recordUploadedPhoto({
    required OwnerPropertyPhotoDraft photo,
    required PropertyImageModel image,
  }) async {
    if (!mounted) return;
    final List<OwnerPropertyPhotoDraft> photos = List.of(_form.photoDrafts);
    final int index = photos.indexWhere(
      (candidate) => candidate.reference == photo.reference,
    );
    if (index < 0) return;
    photos[index] = OwnerPropertyPhotoDraft(
      existingId: image.id,
      existingUrl: image.image,
      name: image.name,
      description: image.description,
      contentFingerprint: photo.contentFingerprint,
      draftKey: photo.reference,
    );
    _formNotifier.value = _form.copyWith(photoDrafts: photos);
    _savedForm = _form;
    final PropertyDetailsModel? property = _savedProperty;
    if (property != null) {
      _savedProperty = property.copyWith(
        images: [
          if (image.id == property.mainImageId) image,
          ...property.images.where(
            (existing) =>
                existing.id != image.id && existing.image != image.image,
          ),
          if (image.id != property.mainImageId) image,
        ],
      );
    }
    await _persistDraft();
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<void>(
    future: _draftRequest,
    builder: (context, snapshot) {
      if (snapshot.hasError) {
        return AppScaffold(
          title: LocaleKeys.ownerAddPropertyTitle,
          body: ExceptionView(
            msg: LocaleKeys.freeDraftLoadFailed,
            onRetry: () async {
              // Recovery gates all editor fields and page state as one coherent screen.
              setState(() => _draftRequest = _restoreDraft());
              await _draftRequest;
            },
          ),
        );
      }
      if (snapshot.connectionState != ConnectionState.done) {
        return AppScaffold(
          title: LocaleKeys.ownerAddPropertyTitle,
          body: const Center(child: CircularProgressIndicator()),
        );
      }
      return _buildFlow(context);
    },
  );

  Widget _buildFlow(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: _isSubmitting,
      builder: (context, isSubmitting, _) => UnsavedChangesGuard(
        hasChanges: () => _hasChanges,
        confirmLeave: _confirmLeave,
        isSaving: () => _isSubmitting.value,
        child: ValueListenableBuilder<int>(
          valueListenable: _currentStep,
          builder: (context, step, _) => AppScaffold(
            title: switch (step) {
              0 =>
                _isEditing
                    ? LocaleKeys.ownerPropertiesEditTitle
                    : LocaleKeys.ownerAddPropertyTitle,
              1 => LocaleKeys.ownerPropertiesPhotos,
              2 => LocaleKeys.ownerAddPropertyPricingTitle,
              _ => null,
            },
            titleWidget: step == 0
                ? _listenToForm(
                    (form) => AppText(
                      RentalOfferLabels.formTitle(
                        form.rentalScope,
                        editing: _isEditing,
                      ),
                      fontWeight: FontWeight.bold,
                    ),
                  )
                : null,
            showBackButton: step < 3,
            actions: [
              if (step < 3 && UserModel.currentUser?.id.isNotEmpty == true)
                IconButton(
                  tooltip: LocaleKeys.rentalSaveLocalDraft,
                  icon: const Icon(Icons.save_outlined),
                  onPressed: isSubmitting
                      ? null
                      : () async {
                          try {
                            await _persistDraft();
                            if (mounted) {
                              Messages.showToast(
                                msg: LocaleKeys.rentalDraftSaved,
                              );
                            }
                          } catch (_) {
                            Messages.showToast(
                              msg: LocaleKeys.freeLocalSaveFailed,
                            );
                          }
                        },
                ),
            ],
            onBack: () {
              if (step == 0) {
                Go.mayPop;
              } else {
                _goToPage(step - 1);
              }
            },
            isBackEnabled: !isSubmitting,
            backgroundColor: context.appColor(
              AppColors.scaffoldBackground,
              surface: true,
            ),
            body: _draftAwareBody(
              child: AbsorbPointer(
                absorbing: isSubmitting,
                child: PageView(
                  controller: _pageController,
                  physics: const NeverScrollableScrollPhysics(),
                  children: [
                    _listenToForm(
                      (form) => AddPropertyBasicsPage(
                        key: ValueKey((
                          form.rentalScope,
                          form.selectedOffer?.reference,
                        )),
                        form: form,
                        onFormChanged: (changed) => _updateForm(() => changed),
                        rentalScopeSelector: RentalScopeSelector(
                          inventory: form.rentalInventory,
                          selectedScope: form.rentalScope,
                          showLocalNotice: false,
                          selectedOfferPersisted:
                              form.selectedOffer?.id.isNotEmpty == true,
                          onScopeSelected: (scope) {
                            FocusManager.instance.primaryFocus?.unfocus();
                            _updateForm(
                              () => OwnerAccommodationDraftData.chooseScope(
                                _form,
                                scope,
                              ),
                            );
                          },
                          onChanged: (inventory) => _updateForm(
                            () => _form.copyWith(rentalInventory: inventory),
                          ),
                          onLegacy: () => _updateForm(
                            () => _form.copyWith(clearRentalInventory: true),
                          ),
                        ),
                        titleController: _titleController,
                        streetController: _streetController,
                        bedroomsController: _bedroomsController,
                        bathroomsController: _bathroomsController,
                        spaceController: _spaceController,
                        floorController: _floorController,
                        selectedGovernorate: _selectedGovernorate,
                        selectedCity: _selectedCity,
                        locationDropdownGeneration: _locationDropdownGeneration,
                        onPropertyTypeSelected: (value) => _updateForm(
                          () => _form.copyWith(
                            propertyType: value.name,
                            propertyTypeValue: value.slug,
                          ),
                        ),
                        onTitleChanged: (value) =>
                            _updateForm(() => _form.copyWith(title: value)),
                        onGovernorateChanged: _selectGovernorate,
                        onCityChanged: _selectCity,
                        onStreetChanged: (value) => _updateForm(
                          () => _form.copyWith(
                            street: value,
                            clearLocation: true,
                          ),
                        ),
                        onBedroomsChanged: (value) =>
                            _updateForm(() => _form.copyWith(bedrooms: value)),
                        onBathroomsChanged: (value) =>
                            _updateForm(() => _form.copyWith(bathrooms: value)),
                        onSpaceChanged: (value) =>
                            _updateForm(() => _form.copyWith(space: value)),
                        onFloorChanged: (value) =>
                            _updateForm(() => _form.copyWith(floor: value)),
                        onLocationSelected: _selectLocation,
                        onNext: () => _goToPage(1),
                      ),
                    ),
                    _listenToForm(
                      (form) => AddPropertyPhotosPage(
                        form: form,
                        photos: form.photoDrafts,
                        onFormChanged: (changed) => _updateForm(() => changed),
                        isReady: form.isPhotosReady,
                        onAddPhotos: _addPhotos,
                        onRemovePhoto: _removePhoto,
                        onReplacePhoto: _replacePhoto,
                        onMainPhotoSelected: _selectMainPhoto,
                        onPhotoMoved: _movePhoto,
                        onVideoSelected: (file, durationSeconds) => _updateForm(
                          () => _form.copyWith(
                            videoFile: file,
                            videoDuration: durationSeconds,
                            removeVideo: false,
                          ),
                        ),
                        onVideoRemoved: () => _updateForm(
                          () => _form.copyWith(
                            clearVideo: true,
                            removeVideo: true,
                          ),
                        ),
                        onVideoPreparingChanged: (preparing) =>
                            _formNotifier.value = _form.copyWith(
                              isVideoPreparing: preparing,
                            ),
                        onPhotoNameChanged: (index, value) =>
                            _updatePhotoMetadata(index: index, name: value),
                        onPhotoDescriptionChanged: (index, value) =>
                            _updatePhotoMetadata(
                              index: index,
                              description: value,
                            ),
                        onNext: () => _goToPage(2),
                      ),
                    ),
                    _listenToForm(
                      (form) => AddPropertyPricingPage(
                        form: form,
                        listingAssistant: form.rentalInventory != null
                            ? null
                            : ListingAiEntry(
                                form: form,
                                propertyId:
                                    (_savedProperty ?? widget.property)?.id ??
                                    '',
                                onApplied: (suggestion) {
                                  _titleController.text =
                                      suggestion.suggestedTitle;
                                  _descriptionController.text =
                                      suggestion.suggestedDescription;
                                  _updateForm(
                                    () => _form.copyWith(
                                      title: suggestion.suggestedTitle,
                                      description:
                                          suggestion.suggestedDescription,
                                    ),
                                  );
                                },
                              ),
                        monthlyPriceController: _monthlyPriceController,
                        rentalDurationController: _rentalDurationController,
                        descriptionController: _descriptionController,
                        onMonthlyPriceChanged: (value) => _updateForm(
                          () => _form.copyWith(monthlyPrice: value),
                        ),
                        onRentalDurationChanged: (value) => _updateForm(
                          () => _form.copyWith(rentalDuration: value),
                        ),
                        onRentalUnitChanged: (value) => _updateForm(
                          () => _form.copyWith(rentalUnit: value),
                        ),
                        onAmenityToggled: _toggleAmenity,
                        onDescriptionChanged: (value) => _updateForm(
                          () => _form.copyWith(description: value),
                        ),
                        onSuitableForSelected: (value) => _updateForm(
                          () => _form.copyWith(suitableFor: value),
                        ),
                        isSubmitting: isSubmitting,
                        onOptionLabelsLoaded: (labels) {
                          _formNotifier.value = _form.copyWith(
                            optionLabels: labels,
                          );
                        },
                        onNext: _reviewAndSubmit,
                        onAdditionalDetailsChanged: (form) =>
                            _updateForm(() => form),
                      ),
                    ),
                    if (!_isEditing)
                      _listenToForm(
                        (form) => AddPropertySubmittedPage(
                          message: _submissionMessage,
                          summaryItems: form.submittedSummary,
                          onAddAnother: _resetFlow,
                        ),
                      ),
                  ],
                  onPageChanged: (step) {
                    _currentStep.value = step;
                    _scheduleDraft();
                  },
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _draftAwareBody({required Widget child}) => SafeArea(
    child: Column(
      children: [
        OwnerDraftStatus(
          cubit: _draftCubit,
          form: _formNotifier,
          uploadProgress: _uploadPropertyImagesCubit?.progress,
          retry: () async {
            try {
              await _persistDraft();
            } catch (_) {
              if (mounted) {
                Messages.showToast(msg: LocaleKeys.freeLocalSaveFailed);
              }
            }
          },
        ),
        Expanded(child: child),
      ],
    ),
  );

  Widget _listenToForm(
    Widget Function(OwnerAddPropertyFormState form) builder,
  ) {
    return ValueListenableBuilder<OwnerAddPropertyFormState>(
      valueListenable: _formNotifier,
      builder: (context, form, _) => builder(form),
    );
  }
}
