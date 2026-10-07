import 'dart:io';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_listing_summary.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_offer.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_room.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_terms.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/owner/home/data/owner_add_property_mapper.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

const offersEnabled = RentalOfferCapabilities(
  contractVersion: 1,
  inventoryWrites: true,
  search: true,
  favorites: true,
  viewings: true,
  mediaAssociations: true,
  inventoryActions: true,
);
const offerTerms = RentalTerms(
  price: '1500',
  pricePeriod: 'monthly',
  minimumMonths: 3,
  deposit: 'one_month',
  suitableFor: 'students',
  description: 'Quiet accommodation near transport',
  smokingAllowed: false,
  rules: ['Keep shared spaces clean'],
);
const rentalRooms = [
  RentalRoom(
    id: 'room-a',
    name: 'الغرفة أ',
    capacity: 2,
    bathroomAccess: 'shared',
    mediaIds: ['photo-a'],
    beds: [
      RentalBed(id: 'bed-a1', name: 'السرير أ١'),
      RentalBed(id: 'bed-a2', name: 'السرير أ٢'),
    ],
  ),
  RentalRoom(
    id: 'room-b',
    name: 'الغرفة ب',
    capacity: 1,
    bathroomAccess: 'private',
    mediaIds: ['photo-b'],
  ),
  RentalRoom(id: 'room-c', name: 'الغرفة ج', capacity: 1),
];
const bedOffer = RentalOffer(
  id: 'offer-bed-a1',
  scopeValue: 'bed',
  name: 'عرض السرير أ١',
  roomRefs: ['room-a'],
  bedRef: 'bed-a1',
  terms: offerTerms,
  availability: 'available',
  revision: 7,
  canArchive: true,
  canSetAvailability: true,
  link: 'https://sokoun.app/properties/property-a/offers/offer-bed-a1',
);
const independentRooms = [
  RentalOffer(
    id: 'offer-room-a',
    scopeValue: 'room',
    name: 'عرض الغرفة أ',
    roomRefs: ['room-a'],
    terms: offerTerms,
    availability: 'available',
    revision: 3,
  ),
  RentalOffer(
    id: 'offer-room-b',
    scopeValue: 'room',
    name: 'عرض الغرفة ب',
    roomRefs: ['room-b'],
    terms: RentalTerms(
      price: '2200',
      pricePeriod: 'weekly',
      minimumMonths: 1,
      deposit: 'none',
      suitableFor: 'all',
      description: 'An independent room with a private bathroom',
    ),
    availability: 'available',
    revision: 4,
  ),
];
const groupOffer = RentalOffer(
  id: 'offer-group',
  scopeValue: 'room_group',
  name: 'الغرفتان معًا',
  roomRefs: ['room-a', 'room-b'],
  terms: RentalTerms(
    price: '5000',
    pricePeriod: 'monthly',
    minimumMonths: 6,
    deposit: 'one_month',
    suitableFor: 'all',
    description: 'Two identified rooms rented together',
  ),
  availability: 'available',
  revision: 8,
);
const wholeOffer = RentalOffer(
  id: 'offer-whole',
  scopeValue: 'entire_property',
  terms: offerTerms,
  availability: 'available',
  revision: 5,
);
RentalInventory rentalInventory({
  List<RentalOffer> offers = const [bedOffer],
  String mode = 'partial',
}) => RentalInventory(
  mode: mode,
  revision: 12,
  rooms: mode == 'whole' ? const [] : rentalRooms,
  offers: offers,
  sharedMediaIds: const ['photo-shared'],
);
PropertyDetailsModel rentalProperty({
  RentalInventory? inventory,
  RentalListingSummary? summary,
}) => const PropertyDetailsModel.initial().copyWith(
  id: 'property-a',
  ownerId: 'owner-a',
  owner: 'Owner',
  title: 'شقة بالقرب من المواصلات',
  propertyType: 'apartment',
  price: '9000',
  pricePeriod: 'monthly',
  description: 'Physical property description',
  rentalPeriod: 12,
  suitableFor: 'all',
  bedrooms: 3,
  bathrooms: 2,
  area: 120,
  street: 'Example street',
  district: 'Example district',
  latitude: '30.04',
  longitude: '31.23',
  video: 'https://example.com/tour.mp4',
  videoDuration: 35,
  status: 'under_review',
  ownershipProof: 'https://private.example.com/proof.jpg',
  amenities: const ['wifi', 'balcony'],
  rentalInventory: inventory,
  rentalSummary: summary,
  mainImage: 'https://example.com/a.jpg',
  mainImageId: 'photo-a',
  images: [
    PropertyImageModel.initial().copyWith(
      id: 'photo-a',
      image: 'https://example.com/a.jpg',
      name: 'الغرفة أ',
    ),
    PropertyImageModel.initial().copyWith(
      id: 'photo-b',
      image: 'https://example.com/b.jpg',
      name: 'الغرفة ب',
    ),
    PropertyImageModel.initial().copyWith(
      id: 'photo-shared',
      image: 'https://example.com/shared.jpg',
      name: 'المطبخ المشترك',
    ),
  ],
);
OwnerAddPropertyFormState rentalForm(
  RentalInventory inventory, {
  bool creating = false,
}) {
  final seed = OwnerAddPropertyMapper.fromProperty(
    rentalProperty(inventory: inventory),
  ).form;
  return seed.copyWith(
    governorateId: 'g',
    governorate: 'Cairo',
    districtId: 'c',
    district: 'Nasr City',
    submissionKey: 'stable-submission-key',
    photoDrafts: [
      ...seed.photoDrafts,
      for (var i = seed.photoCount; i < 10; i++)
        OwnerPropertyPhotoDraft(file: File('/tmp/fixture-$i.jpg')),
    ],
    videoFile: creating ? File('/tmp/fixture-tour.mp4') : null,
    videoDuration: 35,
  );
}
