import 'dart:io';

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

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
    final PropertyDetailsModel? property = widget.property;
    _form = property == null
        ? OwnerAddPropertyFormState.initial()
        : _formFromProperty(property);
    _selectedGovernorate = property == null
        ? null
        : _governorateFromProperty(property);
    _selectedCity = property == null ? null : _cityFromProperty(property);
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

  OwnerAddPropertyFormState _formFromProperty(PropertyDetailsModel property) {
    final Set<String> amenities = property.amenityLabels
        .where(OwnerAddPropertyContent.amenityOptions.contains)
        .toSet();
    if (property.isFurnished) {
      amenities.add('مفروش');
    }
    final List<String> locationParts = [
      property.district,
      property.city.name,
      property.city.governorateName,
    ].where((part) => part.trim().isNotEmpty).toList(growable: false);

    return OwnerAddPropertyFormState.initial().copyWith(
      title: property.title,
      propertyType: property.propertyTypeLabel,
      governorate: property.city.governorateName,
      district: property.city.name.isNotEmpty
          ? property.city.name
          : property.district,
      street: property.street.isNotEmpty ? property.street : property.district,
      bedrooms: _positiveNumberText(property.bedrooms),
      bathrooms: _positiveNumberText(property.bathrooms),
      space: property.space.isNotEmpty
          ? property.space
          : _positiveNumberText(property.area),
      floor: property.floor.toString(),
      buildingYear: _positiveNumberText(property.buildingYear),
      mapQuery: locationParts.join('، '),
      isLocationSelected: locationParts.isNotEmpty,
      existingPhotoUrls: property.imageUrls
          .take(OwnerAddPropertyContent.maxPhotoCount)
          .toList(growable: false),
      monthlyPrice: property.price,
      deposit: _depositLabel(property.deposit),
      rentalDuration: _positiveNumberText(property.rentalPeriod),
      rentalUnit: _rentalUnitLabel(property.pricePeriod),
      amenities: amenities,
      description: property.description,
      smokingPolicy: property.smokingAllowed ? 'مسموح' : 'ممنوع',
      suitableFor: _suitableForLabel(property.suitableFor),
      ownershipProofUrl: property.ownershipProof,
    );
  }

  OwnerPropertyLocationModel? _governorateFromProperty(
    PropertyDetailsModel property,
  ) {
    final String id = property.city.governorate;
    final String name = property.city.governorateName;
    if (id.isEmpty && name.isEmpty) {
      return null;
    }
    return OwnerPropertyLocationModel(
      id: id,
      name: name,
      slug: '',
      createdAt: '',
      updatedAt: '',
    );
  }

  OwnerPropertyLocationModel? _cityFromProperty(PropertyDetailsModel property) {
    if (property.city.id.isEmpty && property.city.name.isEmpty) {
      return null;
    }
    return OwnerPropertyLocationModel(
      id: property.city.id,
      name: property.city.name,
      slug: property.city.slug,
      createdAt: property.city.createdAt,
      updatedAt: property.city.updatedAt,
    );
  }

  String _positiveNumberText(num value) => value > 0 ? '$value' : '';

  String _depositLabel(String value) {
    return const {
          'none': 'بدون تأمين',
          '0': 'بدون تأمين',
          'half_month': 'نصف شهر',
          '0.5': 'نصف شهر',
          'one_month': 'شهر واحد',
          '1': 'شهر واحد',
          'two_months': 'شهرين',
          '2': 'شهرين',
        }[value] ??
        (OwnerAddPropertyContent.depositOptions.contains(value) ? value : '');
  }

  String _rentalUnitLabel(String value) {
    return const {
          'daily': 'يوم',
          'weekly': 'أسبوع',
          'monthly': 'شهر',
          'yearly': 'سنة',
        }[value] ??
        (OwnerAddPropertyContent.rentalUnitOptions.contains(value)
            ? value
            : 'شهر');
  }

  String _suitableForLabel(String value) {
    return const {
          'all': 'الكل',
          'males_only': 'ولاد فقط',
          'females_only': 'بنات فقط',
          'families': 'عائلات',
          'individuals': 'أفراد',
          'shared': 'مشاركة',
        }[value] ??
        (OwnerAddPropertyContent.suitableForOptions.contains(value)
            ? value
            : '');
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
    if (_selectedGovernorate == governorate) {
      return;
    }
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
    if (_selectedCity == city) {
      return;
    }
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
    final int remaining =
        OwnerAddPropertyContent.maxPhotoCount - _form.photoCount;
    final List<File> selectedPhotos = await Helpers.getImages(limit: remaining);
    if (!mounted || selectedPhotos.isEmpty) {
      return;
    }
    final List<File> photos = [
      ..._form.photos,
      ...selectedPhotos.take(remaining),
    ];
    _updateForm(() => _form.copyWith(photos: photos));
  }

  void _removePhoto(int index) {
    if (index < 0 || index >= _form.photoCount) {
      return;
    }
    if (index < _form.existingPhotoUrls.length) {
      final List<String> existingPhotoUrls = List<String>.of(
        _form.existingPhotoUrls,
      )..removeAt(index);
      _updateForm(() => _form.copyWith(existingPhotoUrls: existingPhotoUrls));
      return;
    }
    final int localPhotoIndex = index - _form.existingPhotoUrls.length;
    final List<File> photos = List<File>.of(_form.photos)
      ..removeAt(localPhotoIndex);
    _updateForm(() => _form.copyWith(photos: photos));
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
    if (_isSubmitting ||
        !_form.isBasicsReady ||
        !_form.isPhotosReady ||
        !_form.isPricingReady ||
        !_form.isExtraDetailsReady) {
      return;
    }
    setState(() => _isSubmitting = true);
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
          updatedProperty = _mergeFormIntoProperty(
            original: property,
            response: response,
          );
          wasSubmitted = true;
        },
      );
    }
    if (!mounted) {
      return;
    }
    setState(() {
      _isSubmitting = false;
      if (wasSubmitted && !_isEditing) {
        _form = _form.copyWith(submittedAt: DateTime.now());
      }
    });
    if (updatedProperty != null) {
      Go.back(updatedProperty);
    } else if (wasSubmitted) {
      _goToPage(5);
    }
  }

  PropertyDetailsModel _mergeFormIntoProperty({
    required PropertyDetailsModel original,
    required PropertyDetailsModel response,
  }) {
    final Map<String, dynamic> body = _form.toRequestBody();
    final List<String> amenities = [
      if (body['has_wifi'] == true) 'wifi',
      if (body['has_elevator'] == true) 'elevator',
      if (body['has_garage'] == true) 'garage',
      if (body['has_security'] == true) 'security',
      if (body['has_balcony'] == true) 'balcony',
      if (body['has_air_conditioning'] == true) 'air_conditioning',
      if (body['near_metro'] == true) 'near_metro',
      if (body['has_natural_gas'] == true) 'natural_gas',
      if (body['has_electricity_meter'] == true) 'electricity_meter',
      if (body['has_water_meter'] == true) 'water_meter',
    ];
    final OwnerPropertyLocationModel? selectedCity = _selectedCity;
    final OwnerPropertyLocationModel? selectedGovernorate =
        _selectedGovernorate;
    final PropertyDetailsModel property = original.copyWith(
      mainImage: response.mainImage.isEmpty
          ? original.mainImage
          : response.mainImage,
      images: response.images.isEmpty ? original.images : response.images,
    );
    final CityModel city = selectedCity == null
        ? property.city
        : property.city.copyWith(
            id: selectedCity.id,
            name: selectedCity.name,
            slug: selectedCity.slug,
            governorate: selectedGovernorate?.id,
            governorateName: selectedGovernorate?.name,
          );

    return property.copyWith(
      title: _form.title.trim(),
      description: _form.description.trim(),
      price: _form.monthlyPrice.trim(),
      pricePeriod: body['price_period'] as String,
      propertyType: body['property_type'] as String,
      isFurnished: body['is_furnished'] as bool,
      bedrooms: int.parse(_form.bedrooms),
      bathrooms: int.parse(_form.bathrooms),
      area: int.parse(_form.space),
      space: _form.space.trim(),
      floor: int.parse(_form.floor),
      rentalPeriod: int.parse(_form.rentalDuration),
      suitableFor: body['suitable_for'] as String,
      smokingAllowed: body['smoking_allowed'] as bool,
      city: city,
      district: _form.district,
      street: _form.street.trim(),
      buildingYear: int.parse(_form.buildingYear),
      deposit: body['deposit'] as String,
      amenities: amenities,
    );
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
                title: _isEditing
                    ? LocaleKeys.ownerPropertiesEditTitle
                    : 'إضافة عقار جديد',
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
                onBack: _isEditing ? Go.back : null,
                onNext: () => _goToPage(1),
              ),
              AddPropertyPhotosPage(
                existingPhotoUrls: _form.existingPhotoUrls,
                photos: _form.photos,
                isReady: _form.isPhotosReady,
                onAddPhotos: _addPhotos,
                onRemovePhoto: _removePhoto,
                onBack: () => _goToPage(0),
                onNext: () => _goToPage(2),
              ),
              AddPropertyVideoPage(
                video: _form.video,
                onVideoSelected: _selectVideo,
                onVideoRemoved: _removeVideo,
                onBack: () => _goToPage(1),
                onNext: () => _goToPage(3),
                onSkip: () => _goToPage(3),
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
                onBack: () => _goToPage(2),
                onNext: () => _goToPage(4),
              ),
              AddPropertyExtraDetailsPage(
                form: _form,
                onSmokingSelected: (value) =>
                    _updateForm(() => _form.copyWith(smokingPolicy: value)),
                onSuitableForSelected: (value) =>
                    _updateForm(() => _form.copyWith(suitableFor: value)),
                onProofUploadTap: _pickOwnershipProof,
                onBack: () => _goToPage(3),
                onNext: _submitForReview,
                isSubmitting: _isSubmitting,
                primaryLabel: _isEditing
                    ? LocaleKeys.ownerPropertiesSaveChanges
                    : null,
              ),
              if (!_isEditing)
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
