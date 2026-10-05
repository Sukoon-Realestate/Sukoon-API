import 'models/property_location.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_location_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_governorate_model.dart';

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
    final Set<String> amenities = property.amenities.toSet();
    if (property.isFurnished) {
      amenities.add('furnished');
    }

    return OwnerPropertyFormSeed(
      governorate: _governorateFromProperty(property),
      city: _cityFromProperty(property),
      form: OwnerAddPropertyFormState.initial().copyWith(
        title: property.title,
        propertyType: _propertyTypeLabel(property.propertyType),
        propertyTypeValue: property.propertyType,
        governorateId: property.governorateId,
        governorate: property.governorateName,
        districtId: property.city.id,
        district: property.city.name.isNotEmpty
            ? property.city.name
            : property.district,
        street: property.street.isNotEmpty
            ? property.street
            : property.district,
        neighborhood: property.district,
        bedrooms: _positiveNumberText(property.bedrooms),
        bathrooms: _positiveNumberText(property.bathrooms),
        space: property.space.isNotEmpty
            ? property.space
            : _positiveNumberText(property.area),
        floor: property.floor?.toString() ?? '',
        location: _locationFromProperty(property),
        photoDrafts: _photoDraftsFromProperty(property),
        monthlyPrice: property.price,
        rentalDuration: _positiveNumberText(property.rentalPeriod),
        rentalUnit: _rentalUnitLabel(property.pricePeriod),
        amenities: amenities,
        description: property.description,
        suitableFor: _suitableForLabel(property.suitableFor),
        videoUrl: property.video ?? '',
        videoDuration: property.videoDuration,
        country: property.country,
        buildingYear: _positiveNumberText(property.buildingYear),
        deposit: property.deposit,
        smokingAllowed: property.smokingAllowed,
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
    final Map<String, dynamic> body = form.toJson(isEditing: true);
    final List<String> amenities = form.amenityApiValues
        .where((value) => value != 'furnished')
        .toList();
    final PropertyDetailsModel property = original.copyWith(
      mainImage: response.mainImage.isEmpty
          ? original.mainImage
          : response.mainImage,
      images: response.images.isEmpty
          ? [
              for (final photo in form.photoDrafts)
                if (photo.isExisting && photo.existingId.isNotEmpty)
                  original.images
                      .firstWhere(
                        (image) => image.id == photo.existingId,
                        orElse: PropertyImageModel.initial,
                      )
                      .copyWith(
                        id: photo.existingId,
                        image: photo.existingUrl,
                        name: photo.name.trim(),
                        description: photo.description.trim(),
                      ),
            ]
          : response.images,
      video: response.video ?? original.video,
      videoDuration: response.videoDuration ?? original.videoDuration,
      clearVideo: form.removeVideo,
      status: response.status.isEmpty ? 'under_review' : response.status,
      isVerified: response.isVerified,
      isOwnershipVerified: response.isOwnershipVerified,
      updatedAt: response.updatedAt.isEmpty
          ? original.updatedAt
          : response.updatedAt,
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
      city: city,
      governorate: selectedGovernorate == null
          ? property.governorate
          : PropertyGovernorateModel(
              id: selectedGovernorate.id,
              name: selectedGovernorate.name,
              slug: selectedGovernorate.slug,
              createdAt: selectedGovernorate.createdAt,
              updatedAt: selectedGovernorate.updatedAt,
            ),
      district: body['district'] as String,
      latitude: form.location?.latitude.toString() ?? property.latitude,
      longitude: form.location?.longitude.toString() ?? property.longitude,
      street: form.street.trim(),
      amenities: amenities,
      mainImageId: response.mainImageId.isEmpty
          ? form.photoDrafts.firstOrNull?.existingId ?? ''
          : response.mainImageId,
      mainImageName: form.photoDrafts.firstOrNull?.name.trim() ?? '',
      mainImageDescription:
          form.photoDrafts.firstOrNull?.description.trim() ?? '',
      country: form.country.trim(),
      buildingYear: int.tryParse(form.buildingYear) ?? 0,
      deposit: form.deposit.trim(),
      smokingAllowed: form.smokingAllowed,
      clearSmokingAllowed: form.smokingAllowed == null,
      ownershipProof: form.removeOwnershipProof
          ? ''
          : response.ownershipProof.isEmpty
          ? original.ownershipProof
          : response.ownershipProof,
    );
  }

  static PropertyLocation? _locationFromProperty(
    PropertyDetailsModel property,
  ) {
    final location = PropertyLocation.fromJson({
      'latitude': property.latitude,
      'longitude': property.longitude,
    });
    return location.isValid ? location : null;
  }

  static OwnerPropertyLocationModel? _governorateFromProperty(
    PropertyDetailsModel property,
  ) {
    final String id = property.governorateId;
    final String name = property.governorateName;
    if (id.isEmpty && name.isEmpty) return null;
    return OwnerPropertyLocationModel(
      id: id,
      name: name,
      slug: property.governorate.slug,
      createdAt: property.governorate.createdAt,
      updatedAt: property.governorate.updatedAt,
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

  static String _rentalUnitLabel(String value) =>
      {
        'daily': LocaleKeys.ownerAddPropertyDay,
        'weekly': LocaleKeys.ownerAddPropertyWeek,
        'monthly': LocaleKeys.ownerAddPropertyMonth,
        'yearly': LocaleKeys.ownerAddPropertyYear,
      }[value] ??
      value;

  static List<OwnerPropertyPhotoDraft> _photoDraftsFromProperty(
    PropertyDetailsModel property,
  ) {
    final PropertyImageModel main = property.images.firstWhere(
      (image) => image.image == property.mainImage,
      orElse: () => PropertyImageModel.initial().copyWith(
        id: property.mainImageId,
        image: property.mainImage,
        name: property.mainImageName,
        description: property.mainImageDescription,
      ),
    );
    final Set<String> seen = {};
    return [
      for (final image in [main, ...property.images])
        if (image.image.trim().isNotEmpty && seen.add(image.image))
          OwnerPropertyPhotoDraft(
            existingId: image.id,
            existingUrl: image.image,
            name: image.name,
            description: image.description,
          ),
    ];
  }

  static String _suitableForLabel(String value) =>
      {
        'all': LocaleKeys.ownerAddPropertyEveryone,
        'males_only': LocaleKeys.ownerAddPropertyMalesOnly,
        'females_only': LocaleKeys.ownerAddPropertyFemalesOnly,
        'families': LocaleKeys.ownerAddPropertyFamilies,
        'individuals': LocaleKeys.ownerAddPropertyIndividuals,
        'singles': LocaleKeys.ownerAddPropertyIndividuals,
        'shared': LocaleKeys.ownerAddPropertyShared,
      }[value] ??
      value;
}
