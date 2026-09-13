import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class OwnerPropertyFormSeed {
  const OwnerPropertyFormSeed({
    required this.form,
    required this.governorate,
    required this.city,
  });

  final OwnerAddPropertyFormState form;
  final OwnerPropertyLocationModel? governorate;
  final OwnerPropertyLocationModel? city;
}

abstract final class OwnerAddPropertyMapper {
  static OwnerPropertyFormSeed fromProperty(PropertyDetailsModel property) {
    final Set<String> amenities = property.amenities
        .map(_amenityLabel)
        .where(OwnerAddPropertyContent.amenityOptions.contains)
        .toSet();
    if (property.isFurnished) {
      amenities.add(LocaleKeys.ownerAddPropertyFurnished);
    }

    final List<String> locationParts = [
      property.district,
      property.city.name,
      property.city.governorateName,
    ].where((part) => part.trim().isNotEmpty).toList(growable: false);

    return OwnerPropertyFormSeed(
      governorate: _governorateFromProperty(property),
      city: _cityFromProperty(property),
      form: OwnerAddPropertyFormState.initial().copyWith(
        title: property.title,
        propertyType: _propertyTypeLabel(property.propertyType),
        governorateId: property.city.governorate,
        governorate: property.city.governorateName,
        districtId: property.city.id,
        district: property.city.name.isNotEmpty
            ? property.city.name
            : property.district,
        street: property.street.isNotEmpty
            ? property.street
            : property.district,
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
        smokingPolicy: property.smokingAllowed
            ? LocaleKeys.ownerAddPropertyAllowed
            : LocaleKeys.ownerAddPropertyNotAllowed,
        suitableFor: _suitableForLabel(property.suitableFor),
        ownershipProofUrl: property.ownershipProof,
      ),
    );
  }

  static PropertyDetailsModel mergeIntoProperty({
    required PropertyDetailsModel original,
    required PropertyDetailsModel response,
    required OwnerAddPropertyFormState form,
    required OwnerPropertyLocationModel? selectedGovernorate,
    required OwnerPropertyLocationModel? selectedCity,
  }) {
    final Map<String, dynamic> body = form.toRequestBody();
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
      title: form.title.trim(),
      description: form.description.trim(),
      price: form.monthlyPrice.trim(),
      pricePeriod: body['price_period'] as String,
      propertyType: body['property_type'] as String,
      isFurnished: body['is_furnished'] as bool,
      bedrooms: int.parse(form.bedrooms),
      bathrooms: int.parse(form.bathrooms),
      area: int.parse(form.space),
      space: form.space.trim(),
      floor: int.parse(form.floor),
      rentalPeriod: int.parse(form.rentalDuration),
      suitableFor: body['suitable_for'] as String,
      smokingAllowed: body['smoking_allowed'] as bool,
      city: city,
      district: form.district,
      street: form.street.trim(),
      buildingYear: int.parse(form.buildingYear),
      deposit: body['deposit'] as String,
      amenities: amenities,
    );
  }

  static OwnerPropertyLocationModel? _governorateFromProperty(
    PropertyDetailsModel property,
  ) {
    final String id = property.city.governorate;
    final String name = property.city.governorateName;
    if (id.isEmpty && name.isEmpty) return null;
    return OwnerPropertyLocationModel(
      id: id,
      name: name,
      slug: '',
      createdAt: '',
      updatedAt: '',
    );
  }

  static OwnerPropertyLocationModel? _cityFromProperty(
    PropertyDetailsModel property,
  ) {
    if (property.city.id.isEmpty && property.city.name.isEmpty) return null;
    return OwnerPropertyLocationModel(
      id: property.city.id,
      name: property.city.name,
      slug: property.city.slug,
      createdAt: property.city.createdAt,
      updatedAt: property.city.updatedAt,
    );
  }

  static String _positiveNumberText(num value) => value > 0 ? '$value' : '';

  static String _propertyTypeLabel(String value) =>
      {
        'apartment': LocaleKeys.ownerAddPropertyApartment,
        'room': LocaleKeys.ownerAddPropertyRoom,
        'studio': LocaleKeys.ownerAddPropertyStudio,
        'villa': LocaleKeys.ownerAddPropertyVilla,
        'floor': LocaleKeys.ownerAddPropertyWholeFloor,
        'roof': LocaleKeys.ownerAddPropertyRoof,
      }[value] ??
      value;

  static String _amenityLabel(String value) =>
      {
        'wifi': LocaleKeys.ownerAddPropertyWifi,
        'elevator': LocaleKeys.ownerAddPropertyElevator,
        'garage': LocaleKeys.ownerAddPropertyGarage,
        'security': LocaleKeys.ownerAddPropertySecurity,
        'balcony': LocaleKeys.ownerAddPropertyBalcony,
        'air_conditioning': LocaleKeys.ownerAddPropertyAirConditioning,
        'natural_gas': LocaleKeys.ownerAddPropertyNaturalGas,
        'electricity_meter': LocaleKeys.ownerAddPropertyElectricityMeter,
        'water_meter': LocaleKeys.ownerAddPropertyWaterMeter,
        'near_metro': LocaleKeys.ownerAddPropertyNearMetro,
      }[value] ??
      value;

  static String _depositLabel(String value) =>
      {
        'none': LocaleKeys.ownerAddPropertyNoDeposit,
        '0': LocaleKeys.ownerAddPropertyNoDeposit,
        'half_month': LocaleKeys.ownerAddPropertyHalfMonth,
        '0.5': LocaleKeys.ownerAddPropertyHalfMonth,
        'one_month': LocaleKeys.ownerAddPropertyOneMonth,
        '1': LocaleKeys.ownerAddPropertyOneMonth,
        'two_months': LocaleKeys.ownerAddPropertyTwoMonths,
        '2': LocaleKeys.ownerAddPropertyTwoMonths,
      }[value] ??
      (OwnerAddPropertyContent.depositOptions.contains(value) ? value : '');

  static String _rentalUnitLabel(String value) =>
      {
        'daily': LocaleKeys.ownerAddPropertyDay,
        'weekly': LocaleKeys.ownerAddPropertyWeek,
        'monthly': LocaleKeys.ownerAddPropertyMonth,
        'yearly': LocaleKeys.ownerAddPropertyYear,
      }[value] ??
      (OwnerAddPropertyContent.rentalUnitOptions.contains(value)
          ? value
          : LocaleKeys.ownerAddPropertyMonth);

  static String _suitableForLabel(String value) =>
      {
        'all': LocaleKeys.ownerAddPropertyEveryone,
        'males_only': LocaleKeys.ownerAddPropertyMalesOnly,
        'females_only': LocaleKeys.ownerAddPropertyFemalesOnly,
        'families': LocaleKeys.ownerAddPropertyFamilies,
        'individuals': LocaleKeys.ownerAddPropertyIndividuals,
        'shared': LocaleKeys.ownerAddPropertyShared,
      }[value] ??
      (OwnerAddPropertyContent.suitableForOptions.contains(value) ? value : '');
}
