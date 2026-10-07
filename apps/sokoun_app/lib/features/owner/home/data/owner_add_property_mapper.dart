import 'models/property_location.dart';
import 'enums/property_price_period.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_location_model.dart';
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
  static OwnerPropertyFormSeed fromProperty(
    PropertyDetailsModel property, {
    String? offerId,
  }) {
    final inventory = property.rentalInventory;
    final whole = inventory?.mode == 'whole' && inventory!.offers.length == 1
        ? inventory.resolved(inventory.offers.single).terms
        : null;
    final Set<String> amenities = property.amenities.toSet();
    if (property.isFurnished) {
      amenities.add('furnished');
    }

    return OwnerPropertyFormSeed(
      governorate: _governorateFromProperty(property),
      city: _cityFromProperty(property),
      form: OwnerAddPropertyFormState.initial().copyWith(
        rentalInventory: property.rentalInventory,
        selectedOfferRef:
            offerId ??
            property.rentalInventory?.offers.firstOrNull?.reference ??
            '',
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
        space: _positiveNumberText(property.area),
        areaDescription: property.space,
        floor: property.floor?.toString() ?? '',
        location: _locationFromProperty(property),
        photoDrafts: _photoDraftsFromProperty(property),
        monthlyPrice: whole?.price ?? property.price,
        rentalDuration: _positiveNumberText(
          whole?.minimumMonths ?? property.rentalPeriod,
        ),
        rentalUnit: _rentalUnitLabel(
          whole?.pricePeriod ?? property.pricePeriod,
        ),
        amenities: amenities,
        description: whole?.description ?? property.description,
        suitableFor: _suitableForLabel(
          whole?.suitableFor ?? property.suitableFor,
        ),
        videoUrl: property.video ?? '',
        videoDuration: property.videoDuration,
        country: property.country,
        buildingYear: _positiveNumberText(property.buildingYear),
        deposit: whole?.deposit ?? property.deposit,
        smokingAllowed: whole?.smokingAllowed ?? property.smokingAllowed,
        ownershipProofUrl: property.ownershipProof,
      ),
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
      PropertyPricePeriod.fromValue(value)?.label ?? value;

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
        'students': LocaleKeys.ownerAddPropertyStudents,
        'female_students': LocaleKeys.ownerAddPropertyFemaleStudents,
        'shared': LocaleKeys.ownerAddPropertyShared,
      }[value] ??
      value;
}
