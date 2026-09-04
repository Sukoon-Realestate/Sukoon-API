import 'dart:io';

import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';

import '../../data/models/owner_add_property_content.dart';
import '../cubits/create_property_cubit.dart';
import '../widgets/owner_add_property/imports.dart';

class OwnerAddPropertyFlowScreen extends StatefulWidget {
  const OwnerAddPropertyFlowScreen({super.key});

  @override
  State<OwnerAddPropertyFlowScreen> createState() =>
      _OwnerAddPropertyFlowScreenState();
}

class _OwnerAddPropertyFlowScreenState
    extends State<OwnerAddPropertyFlowScreen> {
  late final PageController _pageController;
  CreatePropertyCubit? _createPropertyCubit;
  late OwnerAddPropertyFormState _form;
  OwnerPropertyLocationModel? _selectedGovernorate;
  OwnerPropertyLocationModel? _selectedCity;
  int _locationDropdownGeneration = 0;
  bool _isSubmitting = false;

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
    _form = OwnerAddPropertyFormState.initial();
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
    _createPropertyCubit?.close();
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

  void _updateForm(OwnerAddPropertyFormState Function() update) {
    setState(() => _form = update());
  }

  void _goToPage(int page) {
    _pageController.animateToPage(
      page,
      duration: const Duration(milliseconds: 280),
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
    setState(() {
      _form = OwnerAddPropertyFormState.initial();
      _selectedGovernorate = null;
      _selectedCity = null;
      _locationDropdownGeneration++;
      _syncControllers();
    });
    if (_pageController.hasClients) {
      _pageController.jumpToPage(0);
    }
  }

  void _selectGovernorate(OwnerPropertyLocationModel governorate) {
    _selectedGovernorate = governorate;
    _selectedCity = null;
    _updateForm(
      () => _form.copyWith(
        governorate: governorate.name,
        district: '',
        mapQuery: governorate.name,
        isLocationSelected: false,
      ),
    );
    _mapQueryController.text = governorate.name;
  }

  void _selectCity(OwnerPropertyLocationModel city) {
    _selectedCity = city;
    final query = '${city.name}، ${_form.governorate}';
    _updateForm(
      () => _form.copyWith(
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
    final List<File> selectedPhotos = await Helpers.getImages();
    if (!mounted || selectedPhotos.isEmpty) {
      return;
    }
    final int remaining =
        OwnerAddPropertyContent.maxPhotoCount - _form.photoCount;
    final List<File> photos = [
      ..._form.photos,
      ...selectedPhotos.take(remaining),
    ];
    _updateForm(() => _form.copyWith(photos: photos));
  }

  void _removePhoto(int index) {
    if (index < 0 || index >= _form.photos.length) {
      return;
    }
    final List<File> photos = List<File>.of(_form.photos)..removeAt(index);
    _updateForm(() => _form.copyWith(photos: photos));
  }

  Future<void> _pickOwnershipProof() async {
    final File? proof = await Helpers.getImage();
    if (!mounted || proof == null) {
      return;
    }
    _updateForm(() => _form.copyWith(ownershipProof: proof));
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
    if (_isSubmitting ||
        !_form.isBasicsReady ||
        !_form.isPhotosReady ||
        !_form.isPricingReady ||
        !_form.isExtraDetailsReady) {
      return;
    }
    setState(() => _isSubmitting = true);
    bool wasCreated = false;
    final CreatePropertyCubit cubit = _createPropertyCubit ??=
        CreatePropertyCubit();
    await cubit.createProperty(form: _form, onSuccess: () => wasCreated = true);
    if (!mounted) {
      return;
    }
    setState(() {
      _isSubmitting = false;
      if (wasCreated) {
        _form = _form.copyWith(submittedAt: DateTime.now());
      }
    });
    if (wasCreated) {
      _goToPage(4);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: PageView(
            controller: _pageController,
            physics: const NeverScrollableScrollPhysics(),
            children: [
              AddPropertyBasicsPage(
                form: _form,
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
                onNext: () => _goToPage(1),
              ),
              AddPropertyPhotosPage(
                photos: _form.photos,
                isReady: _form.isPhotosReady,
                onAddPhotos: _addPhotos,
                onRemovePhoto: _removePhoto,
                onBack: () => _goToPage(0),
                onNext: () => _goToPage(2),
              ),
              AddPropertyPricingPage(
                form: _form,
                monthlyPriceController: _monthlyPriceController,
                rentalDurationController: _rentalDurationController,
                descriptionController: _descriptionController,
                onMonthlyPriceChanged: (value) =>
                    _updateForm(() => _form.copyWith(monthlyPrice: value)),
                onDepositChanged: (value) =>
                    _updateForm(() => _form.copyWith(deposit: value)),
                onRentalDurationChanged: (value) =>
                    _updateForm(() => _form.copyWith(rentalDuration: value)),
                onRentalUnitChanged: (value) =>
                    _updateForm(() => _form.copyWith(rentalUnit: value)),
                onAmenityToggled: _toggleAmenity,
                onDescriptionChanged: (value) =>
                    _updateForm(() => _form.copyWith(description: value)),
                onBack: () => _goToPage(1),
                onNext: () => _goToPage(3),
              ),
              AddPropertyExtraDetailsPage(
                form: _form,
                onSmokingSelected: (value) =>
                    _updateForm(() => _form.copyWith(smokingPolicy: value)),
                onSuitableForSelected: (value) =>
                    _updateForm(() => _form.copyWith(suitableFor: value)),
                onProofUploadTap: _pickOwnershipProof,
                onBack: () => _goToPage(2),
                onNext: _submitForReview,
                isSubmitting: _isSubmitting,
              ),
              AddPropertySubmittedPage(
                summaryItems: _form.submittedSummary,
                onAddAnother: _resetFlow,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
