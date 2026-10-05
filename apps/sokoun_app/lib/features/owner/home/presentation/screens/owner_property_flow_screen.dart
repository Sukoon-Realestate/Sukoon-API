import '../../data/models/property_location.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
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
  const OwnerPropertyFlowScreen({super.key, this.property});

  final PropertyDetailsModel? property;

  @override
  State<OwnerPropertyFlowScreen> createState() =>
      _OwnerPropertyFlowScreenState();
}

class _OwnerPropertyFlowScreenState extends State<OwnerPropertyFlowScreen> {
  late final PageController _pageController;
  final ValueNotifier<int> _currentStep = ValueNotifier(0);
  PropertySubmissionCubit? _submissionCubit;
  UploadPropertyImagesCubit? _uploadPropertyImagesCubit;
  PropertyDetailsModel? _savedProperty;
  OwnerAddPropertyFormState? _savedForm;
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
        : OwnerAddPropertyMapper.fromProperty(property);
    _formNotifier = ValueNotifier<OwnerAddPropertyFormState>(
      seed?.form ?? OwnerAddPropertyFormState.initial(),
    );
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
  }

  @override
  void dispose() {
    _pageController.dispose();
    _currentStep.dispose();
    _formNotifier.dispose();
    _isSubmitting.dispose();
    _submissionCubit?.close();
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

  bool get _isEditing => widget.property != null;

  OwnerAddPropertyFormState get _form => _formNotifier.value;

  void _updateForm(OwnerAddPropertyFormState Function() update) {
    if (_isSubmitting.value) return;
    _hasChanges = true;
    _formNotifier.value = update();
  }

  void _goToPage(int page) {
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
    FocusManager.instance.primaryFocus?.unfocus();
    try {
      final action = await showModalBottomSheet<PropertyReviewAction>(
        context: context,
        isScrollControlled: true,
        useSafeArea: true,
        showDragHandle: true,
        backgroundColor: AppColors.white,
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
    }
  }

  void _syncControllers() {
    _titleController.text = _form.title;
    _streetController.text = _form.street;
    _bedroomsController.text = _form.bedrooms;
    _bathroomsController.text = _form.bathrooms;
    _spaceController.text = _form.space;
    _floorController.text = _form.floor;
    _monthlyPriceController.text = _form.monthlyPrice;
    _rentalDurationController.text = _form.rentalDuration;
    _descriptionController.text = _form.description;
  }

  void _resetFlow() {
    _hasChanges = false;
    _savedProperty = null;
    _savedForm = null;
    _selectedGovernorate = null;
    _selectedCity = null;
    _locationDropdownGeneration++;
    _formNotifier.value = OwnerAddPropertyFormState.initial();
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
    if (_form.photoCount >= OwnerAddPropertyContent.maxPhotoCount) {
      return;
    }
    final int remaining =
        OwnerAddPropertyContent.maxPhotoCount - _form.photoCount;
    final List<File> selectedPhotos = await Helpers.getImages(limit: remaining);
    if (!mounted || selectedPhotos.isEmpty) {
      return;
    }
    final List<OwnerPropertyPhotoDraft> photoDrafts = [
      ..._form.photoDrafts,
      ...selectedPhotos
          .take(remaining)
          .map((photo) => OwnerPropertyPhotoDraft(file: photo)),
    ];
    _updateForm(() => _form.copyWith(photoDrafts: photoDrafts));
  }

  void _removePhoto(int index) {
    if (index < 0 || index >= _form.photoCount) {
      return;
    }
    if (!_form.photoDrafts[index].canRemove) return;
    final List<OwnerPropertyPhotoDraft> photoDrafts =
        List<OwnerPropertyPhotoDraft>.of(_form.photoDrafts)..removeAt(index);
    _updateForm(() => _form.copyWith(photoDrafts: photoDrafts));
  }

  Future<void> _replacePhoto(int index) async {
    if (index < 0 || index >= _form.photoCount) return;
    final OwnerPropertyPhotoDraft current = _form.photoDrafts[index];
    final File? replacement = await Helpers.getImage();
    if (!mounted || replacement == null) return;
    final List<OwnerPropertyPhotoDraft> photoDrafts =
        List<OwnerPropertyPhotoDraft>.of(_form.photoDrafts);
    photoDrafts[index] = current.copyWith(
      file: replacement,
      existingId: '',
      existingUrl: '',
    );
    _updateForm(() => _form.copyWith(photoDrafts: photoDrafts));
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
        onPhotoUploaded: _recordUploadedPhoto,
        onSuccess: () => wasSubmitted = true,
      );
    } finally {
      if (mounted) _isSubmitting.value = false;
    }
    if (!mounted || !wasSubmitted) return;
    _hasChanges = false;
    if (_isEditing) {
      await showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        useSafeArea: true,
        showDragHandle: true,
        builder: (_) => const PropertyEditReviewSheet(),
      );
      if (!mounted) return;
      Go.back(_savedProperty);
    } else {
      _formNotifier.value = _form.copyWith(submittedAt: DateTime.now());
      _goToPage(3);
    }
  }

  Future<bool> _saveProperty() async {
    final OwnerAddPropertyFormState form = _form;
    if (identical(_savedForm, form)) return true;
    final PropertyDetailsModel? property = _savedProperty ?? widget.property;
    bool wasSaved = false;
    final PropertySubmissionCubit cubit = _submissionCubit ??=
        PropertySubmissionCubit();
    await cubit.save(
      propertyId: property?.id,
      form: form,
      onSuccess: (response) {
        if (!mounted) return;
        _savedProperty = property == null
            ? response
            : OwnerAddPropertyMapper.mergeIntoProperty(
                original: property,
                response: response,
                form: form,
                selectedGovernorate: _selectedGovernorate,
                selectedCity: _selectedCity,
              );
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
          _recordUploadedPhoto(photo: mainPhoto!, image: main);
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
    if (wasSaved) _savedForm = _form;
    return wasSaved;
  }

  void _recordUploadedPhoto({
    required OwnerPropertyPhotoDraft photo,
    required PropertyImageModel image,
  }) {
    if (!mounted) return;
    final List<OwnerPropertyPhotoDraft> photos = List.of(_form.photoDrafts);
    final int index = photos.indexOf(photo);
    if (index < 0) return;
    photos[index] = OwnerPropertyPhotoDraft(
      existingId: image.id,
      existingUrl: image.image,
      name: photo.name.trim(),
      description: photo.description.trim(),
    );
    _formNotifier.value = _form.copyWith(photoDrafts: photos);
    _savedForm = _form;
    final PropertyDetailsModel? property = _savedProperty;
    if (property != null) {
      _savedProperty = property.copyWith(
        images: [
          ...property.images.where((existing) => existing.image != image.image),
          image.copyWith(
            name: photo.name.trim(),
            description: photo.description.trim(),
          ),
        ],
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: _isSubmitting,
      builder: (context, isSubmitting, _) => UnsavedChangesGuard(
        hasChanges: () => _hasChanges,
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
            showBackButton: step < 3,
            onBack: () {
              if (step == 0) {
                Go.mayPop;
              } else {
                _goToPage(step - 1);
              }
            },
            isBackEnabled: !isSubmitting,
            backgroundColor: AppColors.scaffoldBackground,
            body: SafeArea(
              child: AbsorbPointer(
                absorbing: isSubmitting,
                child: PageView(
                  controller: _pageController,
                  physics: const NeverScrollableScrollPhysics(),
                  children: [
                    _listenToForm(
                      (form) => AddPropertyBasicsPage(
                        form: form,
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
                        isReady: form.isPhotosReady,
                        onAddPhotos: _addPhotos,
                        onRemovePhoto: _removePhoto,
                        onReplacePhoto: _replacePhoto,
                        onMainPhotoSelected: _selectMainPhoto,
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
                          summaryItems: form.submittedSummary,
                          onAddAnother: _resetFlow,
                        ),
                      ),
                  ],
                  onPageChanged: (step) => _currentStep.value = step,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _listenToForm(
    Widget Function(OwnerAddPropertyFormState form) builder,
  ) {
    return ValueListenableBuilder<OwnerAddPropertyFormState>(
      valueListenable: _formNotifier,
      builder: (context, form, _) => builder(form),
    );
  }
}
