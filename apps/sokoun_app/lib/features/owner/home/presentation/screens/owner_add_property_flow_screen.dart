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
import '../../data/models/owner_add_property_content.dart';
import '../cubits/create_property_cubit.dart';
import '../cubits/update_property_cubit.dart';
import '../widgets/owner_add_property/imports.dart';

class OwnerAddPropertyFlowScreen extends StatelessWidget {
  const OwnerAddPropertyFlowScreen({super.key});

  @override
  Widget build(BuildContext context) => const OwnerPropertyFlowScreen();
}

class OwnerPropertyFlowScreen extends StatefulWidget {
  const OwnerPropertyFlowScreen({super.key, this.property});

  final PropertyDetailsModel? property;

  @override
  State<OwnerPropertyFlowScreen> createState() =>
      _OwnerPropertyFlowScreenState();
}

class _OwnerPropertyFlowScreenState extends State<OwnerPropertyFlowScreen> {
  late final PageController _pageController;
  CreatePropertyCubit? _createPropertyCubit;
  UpdatePropertyCubit? _updatePropertyCubit;
  late final ValueNotifier<OwnerAddPropertyFormState> _formNotifier;
  OwnerPropertyLocationModel? _selectedGovernorate;
  OwnerPropertyLocationModel? _selectedCity;
  int _locationDropdownGeneration = 0;
  final ValueNotifier<bool> _isSubmitting = ValueNotifier<bool>(false);
  bool _hasChanges = false;

  late final TextEditingController _titleController;
  late final TextEditingController _streetController;
  late final TextEditingController _bedroomsController;
  late final TextEditingController _bathroomsController;
  late final TextEditingController _spaceController;
  late final TextEditingController _floorController;
  late final TextEditingController _buildingYearController;
  late final TextEditingController _mapQueryController;
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
    _buildingYearController = TextEditingController(text: _form.buildingYear);
    _mapQueryController = TextEditingController(text: _form.mapQuery);
    _monthlyPriceController = TextEditingController(text: _form.monthlyPrice);
    _rentalDurationController = TextEditingController(
      text: _form.rentalDuration,
    );
    _descriptionController = TextEditingController(text: _form.description);
  }

  @override
  void dispose() {
    _pageController.dispose();
    _formNotifier.dispose();
    _isSubmitting.dispose();
    _createPropertyCubit?.close();
    _updatePropertyCubit?.close();
    _titleController.dispose();
    _streetController.dispose();
    _bedroomsController.dispose();
    _bathroomsController.dispose();
    _spaceController.dispose();
    _floorController.dispose();
    _buildingYearController.dispose();
    _mapQueryController.dispose();
    _monthlyPriceController.dispose();
    _rentalDurationController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  bool get _isEditing => widget.property != null;

  OwnerAddPropertyFormState get _form => _formNotifier.value;

  void _updateForm(OwnerAddPropertyFormState Function() update) {
    _hasChanges = true;
    _formNotifier.value = update();
  }

  void _goToPage(int page) {
    _pageController.animateToPage(
      page,
      duration: SokounMotion.duration(context, milliseconds: 280),
      curve: Curves.easeOutCubic,
    );
  }

  void _syncControllers() {
    _titleController.text = _form.title;
    _streetController.text = _form.street;
    _bedroomsController.text = _form.bedrooms;
    _bathroomsController.text = _form.bathrooms;
    _spaceController.text = _form.space;
    _floorController.text = _form.floor;
    _buildingYearController.text = _form.buildingYear;
    _mapQueryController.text = _form.mapQuery;
    _monthlyPriceController.text = _form.monthlyPrice;
    _rentalDurationController.text = _form.rentalDuration;
    _descriptionController.text = _form.description;
  }

  void _resetFlow() {
    _hasChanges = false;
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
        mapQuery: governorate.name,
        isLocationSelected: false,
      ),
    );
    _mapQueryController.text = governorate.name;
  }

  void _selectCity(OwnerPropertyLocationModel city) {
    if (_selectedCity == city) {
      return;
    }
    _selectedCity = city;
    final query = '${city.name}، ${_form.governorate}';
    _updateForm(
      () => _form.copyWith(
        districtId: city.id,
        district: city.name,
        mapQuery: query,
        isLocationSelected: false,
      ),
    );
    _mapQueryController.text = query;
  }

  void _selectLocation() {
    final query = _mapQueryController.text.trim().isEmpty
        ? '${_form.district}، ${_form.governorate}'
        : _mapQueryController.text.trim();
    _mapQueryController.text = query;
    _updateForm(
      () => _form.copyWith(mapQuery: query, isLocationSelected: true),
    );
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
    if (current.isExisting) return;
    final File? replacement = await Helpers.getImage();
    if (!mounted || replacement == null) return;
    final List<OwnerPropertyPhotoDraft> photoDrafts =
        List<OwnerPropertyPhotoDraft>.of(_form.photoDrafts);
    photoDrafts[index] = current.copyWith(file: replacement);
    _updateForm(() => _form.copyWith(photoDrafts: photoDrafts));
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

  Future<void> _pickOwnershipProof() async {
    final File? proof = await Helpers.getImage();
    if (!mounted || proof == null) {
      return;
    }
    _updateForm(() => _form.copyWith(ownershipProof: proof));
  }

  void _selectVideo(OwnerPropertyVideoSelection video) {
    _updateForm(() => _form.copyWith(video: video));
  }

  void _removeVideo() {
    _updateForm(() => _form.copyWith(clearVideo: true));
  }

  void _toggleAmenity(String amenity) {
    final amenities = Set<String>.from(_form.amenities);
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
        !_form.isPricingReady ||
        !_form.isExtraDetailsReady) {
      return;
    }
    _isSubmitting.value = true;
    bool wasSubmitted = false;
    PropertyDetailsModel? updatedProperty;
    final PropertyDetailsModel? property = widget.property;
    if (property == null) {
      final CreatePropertyCubit cubit = _createPropertyCubit ??=
          CreatePropertyCubit();
      await cubit.createProperty(
        form: _form,
        onSuccess: () => wasSubmitted = true,
      );
    } else {
      final UpdatePropertyCubit cubit = _updatePropertyCubit ??=
          UpdatePropertyCubit();
      await cubit.updateProperty(
        propertyId: property.id,
        form: _form,
        onSuccess: (response) {
          updatedProperty = OwnerAddPropertyMapper.mergeIntoProperty(
            original: property,
            response: response,
            form: _form,
            selectedGovernorate: _selectedGovernorate,
            selectedCity: _selectedCity,
          );
          wasSubmitted = true;
        },
      );
    }
    if (!mounted) {
      return;
    }
    _isSubmitting.value = false;
    if (wasSubmitted) _hasChanges = false;
    if (wasSubmitted && !_isEditing) {
      _formNotifier.value = _form.copyWith(submittedAt: DateTime.now());
    }
    if (updatedProperty != null) {
      Go.back(updatedProperty);
    } else if (wasSubmitted) {
      _goToPage(5);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: _isSubmitting,
      builder: (context, isSubmitting, _) => UnsavedChangesGuard(
        hasChanges: () => _hasChanges,
        isSaving: () => _isSubmitting.value,
        child: AppScaffold(
          showBackButton: false,
          backgroundColor: AppColors.scaffoldBackground,
          body: SafeArea(
            child: PageView(
              controller: _pageController,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _listenToForm(
                  (form) => AddPropertyBasicsPage(
                    title: _isEditing
                        ? LocaleKeys.ownerPropertiesEditTitle
                        : LocaleKeys.ownerAddPropertyTitle,
                    form: form,
                    titleController: _titleController,
                    streetController: _streetController,
                    bedroomsController: _bedroomsController,
                    bathroomsController: _bathroomsController,
                    spaceController: _spaceController,
                    floorController: _floorController,
                    buildingYearController: _buildingYearController,
                    mapQueryController: _mapQueryController,
                    selectedGovernorate: _selectedGovernorate,
                    selectedCity: _selectedCity,
                    locationDropdownGeneration: _locationDropdownGeneration,
                    onPropertyTypeSelected: (value) =>
                        _updateForm(() => _form.copyWith(propertyType: value)),
                    onTitleChanged: (value) =>
                        _updateForm(() => _form.copyWith(title: value)),
                    onGovernorateChanged: _selectGovernorate,
                    onCityChanged: _selectCity,
                    onStreetChanged: (value) =>
                        _updateForm(() => _form.copyWith(street: value)),
                    onBedroomsChanged: (value) =>
                        _updateForm(() => _form.copyWith(bedrooms: value)),
                    onBathroomsChanged: (value) =>
                        _updateForm(() => _form.copyWith(bathrooms: value)),
                    onSpaceChanged: (value) =>
                        _updateForm(() => _form.copyWith(space: value)),
                    onFloorChanged: (value) =>
                        _updateForm(() => _form.copyWith(floor: value)),
                    onBuildingYearChanged: (value) =>
                        _updateForm(() => _form.copyWith(buildingYear: value)),
                    onMapQueryChanged: (value) => _updateForm(
                      () => _form.copyWith(
                        mapQuery: value,
                        isLocationSelected: false,
                      ),
                    ),
                    onLocationSelected: _selectLocation,
                    onBack: () => Go.mayPop,
                    onNext: () => _goToPage(1),
                  ),
                ),
                _listenToForm(
                  (form) => AddPropertyPhotosPage(
                    photos: form.photoDrafts,
                    isReady: form.isPhotosReady,
                    onAddPhotos: _addPhotos,
                    onRemovePhoto: _removePhoto,
                    onReplacePhoto: _replacePhoto,
                    onPhotoNameChanged: (index, value) =>
                        _updatePhotoMetadata(index: index, name: value),
                    onPhotoDescriptionChanged: (index, value) =>
                        _updatePhotoMetadata(index: index, description: value),
                    onBack: () => _goToPage(0),
                    onNext: () => _goToPage(2),
                  ),
                ),
                _listenToForm(
                  (form) => AddPropertyVideoPage(
                    video: form.video,
                    onVideoSelected: _selectVideo,
                    onVideoRemoved: _removeVideo,
                    onBack: () => _goToPage(1),
                    onNext: () => _goToPage(3),
                    onSkip: () => _goToPage(3),
                  ),
                ),
                _listenToForm(
                  (form) => AddPropertyPricingPage(
                    form: form,
                    monthlyPriceController: _monthlyPriceController,
                    rentalDurationController: _rentalDurationController,
                    descriptionController: _descriptionController,
                    onMonthlyPriceChanged: (value) =>
                        _updateForm(() => _form.copyWith(monthlyPrice: value)),
                    onDepositChanged: (value) =>
                        _updateForm(() => _form.copyWith(deposit: value)),
                    onRentalDurationChanged: (value) => _updateForm(
                      () => _form.copyWith(rentalDuration: value),
                    ),
                    onRentalUnitChanged: (value) =>
                        _updateForm(() => _form.copyWith(rentalUnit: value)),
                    onAmenityToggled: _toggleAmenity,
                    onDescriptionChanged: (value) =>
                        _updateForm(() => _form.copyWith(description: value)),
                    onBack: () => _goToPage(2),
                    onNext: () => _goToPage(4),
                  ),
                ),
                _listenToForm(
                  (form) => AbsorbPointer(
                    absorbing: isSubmitting,
                    child: AddPropertyExtraDetailsPage(
                      form: form,
                      onSmokingSelected: (value) => _updateForm(
                        () => _form.copyWith(smokingPolicy: value),
                      ),
                      onSuitableForSelected: (value) =>
                          _updateForm(() => _form.copyWith(suitableFor: value)),
                      onProofUploadTap: _pickOwnershipProof,
                      onBack: () => _goToPage(3),
                      onNext: _submitForReview,
                      isSubmitting: isSubmitting,
                      primaryLabel: _isEditing
                          ? LocaleKeys.ownerPropertiesSaveChanges
                          : null,
                    ),
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
