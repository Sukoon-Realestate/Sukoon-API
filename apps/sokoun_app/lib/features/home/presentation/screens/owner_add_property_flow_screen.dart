import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../data/models/owner_add_property_content.dart';
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
  late OwnerAddPropertyFormState _form;

  late final TextEditingController _streetController;
  late final TextEditingController _bedroomsController;
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
    _streetController = TextEditingController(text: _form.street);
    _bedroomsController = TextEditingController(text: _form.bedrooms);
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
    _streetController.dispose();
    _bedroomsController.dispose();
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
    _streetController.text = _form.street;
    _bedroomsController.text = _form.bedrooms;
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
      _syncControllers();
    });
    if (_pageController.hasClients) {
      _pageController.jumpToPage(0);
    }
  }

  void _selectGovernorate(String governorate) {
    final districts =
        OwnerAddPropertyContent.districtOptionsByGovernorate[governorate] ??
            const <String>[];

    _updateForm(
          () => _form.copyWith(
        governorate: governorate,
        district: districts.isEmpty ? '' : districts.first,
        mapQuery: governorate,
        isLocationSelected: false,
      ),
    );
    _mapQueryController.text = governorate;
  }

  void _selectDistrict(String district) {
    final query = '$district، ${_form.governorate}';
    _updateForm(
          () => _form.copyWith(
        district: district,
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

  void _addPhoto() {
    if (_form.photoCount >= OwnerAddPropertyContent.maxPhotoCount) {
      return;
    }
    _updateForm(() => _form.copyWith(photoCount: _form.photoCount + 1));
  }

  void _removePhoto() {
    if (_form.photoCount <= 0) {
      return;
    }
    _updateForm(() => _form.copyWith(photoCount: _form.photoCount - 1));
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

  void _submitForReview() {
    setState(() => _form = _form.copyWith(submittedAt: DateTime.now()));
    _goToPage(4);
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
                streetController: _streetController,
                bedroomsController: _bedroomsController,
                spaceController: _spaceController,
                floorController: _floorController,
                buildingYearController: _buildingYearController,
                mapQueryController: _mapQueryController,
                onPropertyTypeSelected: (value) =>
                    _updateForm(() => _form.copyWith(propertyType: value)),
                onGovernorateChanged: _selectGovernorate,
                onDistrictChanged: _selectDistrict,
                onStreetChanged: (value) =>
                    _updateForm(() => _form.copyWith(street: value)),
                onBedroomsChanged: (value) =>
                    _updateForm(() => _form.copyWith(bedrooms: value)),
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
                photoCount: _form.photoCount,
                isReady: _form.isPhotosReady,
                onAddPhoto: _addPhoto,
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
                onProofStatusSelected: (value) =>
                    _updateForm(() => _form.copyWith(proofStatus: value)),
                onProofUploadTap: () =>
                    _updateForm(() => _form.copyWith(proofStatus: 'مرفوع')),
                onBack: () => _goToPage(2),
                onNext: _submitForReview,
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
