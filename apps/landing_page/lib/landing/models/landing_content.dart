import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../theme/landing_theme.dart';

enum Audience { tenant, owner }

class FeatureGroup {
  const FeatureGroup({
    required this.icon,
    required this.title,
    required this.items,
  });

  final String icon;
  final String title;
  final List<String> items;
}

class JourneyStep {
  const JourneyStep({
    required this.number,
    required this.title,
    required this.body,
  });

  final String number;
  final String title;
  final String body;
}

class PropertyItem {
  const PropertyItem({
    required this.title,
    required this.area,
    required this.price,
    required this.rooms,
    required this.squareMeters,
    required this.type,
    required this.imageColor,
    required this.isVerified,
  });

  final String title;
  final String area;
  final String price;
  final String rooms;
  final String squareMeters;
  final String type;
  final Color imageColor;
  final bool isVerified;
}

class FaqItem {
  const FaqItem(this.question, this.answer);

  final String question;
  final String answer;
}

abstract final class LandingContent {
  static List<FeatureGroup> get tenantFeatures => [
    FeatureGroup(
      icon: '🔍',
      title: LocaleKeys.landingFeatureSmartSearchTitle,
      items: [
        LocaleKeys.landingFeaturePropertyTypeArea,
        LocaleKeys.landingFeaturePriceRentalPeriod,
        LocaleKeys.landingFeatureFamiliesIndividuals,
        LocaleKeys.landingFeatureAmenitiesSmoking,
      ],
    ),
    FeatureGroup(
      icon: '🏠',
      title: LocaleKeys.landingFeatureFullDetailsTitle,
      items: [
        LocaleKeys.landingFeatureMediaLocation,
        LocaleKeys.landingFeatureRoomsArea,
        LocaleKeys.landingFeatureHousingRules,
        LocaleKeys.landingFeatureVerificationStatus,
      ],
    ),
    FeatureGroup(
      icon: '❤️',
      title: LocaleKeys.landingFeatureSaveCompareTitle,
      items: [
        LocaleKeys.landingFeatureSaveFavorites,
        LocaleKeys.landingFeatureReturnFavorites,
        LocaleKeys.landingFeatureCompareOptions,
      ],
    ),
    FeatureGroup(
      icon: '💬',
      title: LocaleKeys.landingFeatureSafeChatTitle,
      items: [
        LocaleKeys.landingFeaturePhoneNumbersHidden,
        LocaleKeys.landingFeaturePhotosVoiceMessages,
        LocaleKeys.landingFeatureUnverifiedLimits,
      ],
    ),
    FeatureGroup(
      icon: '📅',
      title: LocaleKeys.landingFeatureBookVisitTitle,
      items: [
        LocaleKeys.landingFeatureChooseDateTime,
        LocaleKeys.landingFeatureTrackRequest,
        LocaleKeys.landingFeatureChangeCancelVisit,
      ],
    ),
  ];

  static List<FeatureGroup> get ownerFeatures => [
    FeatureGroup(
      icon: '📋',
      title: LocaleKeys.landingFeatureOrganizedListingTitle,
      items: [
        LocaleKeys.landingFeatureCompleteDataMap,
        LocaleKeys.landingFeatureRoomsAreaAmenities,
        LocaleKeys.landingFeatureRentalSuitableFor,
        LocaleKeys.landingFeatureSmokingRules,
      ],
    ),
    FeatureGroup(
      icon: '📸',
      title: LocaleKeys.landingFeatureClearMediaTitle,
      items: [
        LocaleKeys.landingFeatureImageNameDescription,
        LocaleKeys.landingFeatureOneMinuteVideo,
        LocaleKeys.landingFeaturePreviewBeforePublish,
      ],
    ),
    FeatureGroup(
      icon: '📄',
      title: LocaleKeys.landingFeatureOwnershipProofTitle,
      items: [
        LocaleKeys.landingFeatureUtilityBill,
        LocaleKeys.landingFeatureOwnershipLeaseContract,
        LocaleKeys.landingFeatureInternalReviewOnly,
      ],
    ),
    FeatureGroup(
      icon: '📬',
      title: LocaleKeys.landingFeatureManageVisitsTitle,
      items: [
        LocaleKeys.landingFeatureAcceptRejectRequests,
        LocaleKeys.landingFeatureOpenTenantChat,
        LocaleKeys.landingFeatureManageAppointments,
      ],
    ),
    FeatureGroup(
      icon: '📊',
      title: LocaleKeys.landingFeatureTrackPerformanceTitle,
      items: [
        LocaleKeys.landingFeatureViewsSaves,
        LocaleKeys.landingFeatureMessagesVisits,
        LocaleKeys.landingFeatureMonthlyAnalytics,
      ],
    ),
    FeatureGroup(
      icon: '🔧',
      title: LocaleKeys.landingFeatureManageStatusTitle,
      items: [
        LocaleKeys.landingFeatureReviewStatuses,
        LocaleKeys.landingFeatureHideEditProperty,
        LocaleKeys.landingFeatureChangeHistory,
      ],
    ),
  ];

  static List<JourneyStep> get tenantSteps => [
    JourneyStep(
      number: '01',
      title: LocaleKeys.landingTenantStepOneTitle,
      body: LocaleKeys.landingTenantStepOneBody,
    ),
    JourneyStep(
      number: '02',
      title: LocaleKeys.landingTenantStepTwoTitle,
      body: LocaleKeys.landingTenantStepTwoBody,
    ),
    JourneyStep(
      number: '03',
      title: LocaleKeys.landingTenantStepThreeTitle,
      body: LocaleKeys.landingTenantStepThreeBody,
    ),
    JourneyStep(
      number: '04',
      title: LocaleKeys.landingTenantStepFourTitle,
      body: LocaleKeys.landingTenantStepFourBody,
    ),
  ];

  static List<JourneyStep> get ownerSteps => [
    JourneyStep(
      number: '01',
      title: LocaleKeys.landingOwnerStepOneTitle,
      body: LocaleKeys.landingOwnerStepOneBody,
    ),
    JourneyStep(
      number: '02',
      title: LocaleKeys.landingOwnerStepTwoTitle,
      body: LocaleKeys.landingOwnerStepTwoBody,
    ),
    JourneyStep(
      number: '03',
      title: LocaleKeys.landingOwnerStepThreeTitle,
      body: LocaleKeys.landingOwnerStepThreeBody,
    ),
    JourneyStep(
      number: '04',
      title: LocaleKeys.landingOwnerStepFourTitle,
      body: LocaleKeys.landingOwnerStepFourBody,
    ),
  ];

  static List<PropertyItem> get properties => [
    PropertyItem(
      title: LocaleKeys.landingPropertyOneTitle,
      area: LocaleKeys.landingPropertyOneArea,
      price: '5,500',
      rooms: '3',
      squareMeters: '120',
      type: LocaleKeys.landingPropertyFamilies,
      imageColor: Color(0xFFCBD5E1),
      isVerified: true,
    ),
    PropertyItem(
      title: LocaleKeys.landingPropertyTwoTitle,
      area: LocaleKeys.landingPropertyTwoArea,
      price: '2,800',
      rooms: '1',
      squareMeters: '55',
      type: LocaleKeys.landingPropertyIndividuals,
      imageColor: Color(0xFFBFDBFE),
      isVerified: true,
    ),
    PropertyItem(
      title: LocaleKeys.landingPropertyThreeTitle,
      area: LocaleKeys.landingPropertyThreeArea,
      price: '1,400',
      rooms: '1',
      squareMeters: '25',
      type: LocaleKeys.landingPropertyIndividuals,
      imageColor: Color(0xFFBBF7D0),
      isVerified: false,
    ),
    PropertyItem(
      title: LocaleKeys.landingPropertyFourTitle,
      area: LocaleKeys.landingPropertyFourArea,
      price: '4,200',
      rooms: '2',
      squareMeters: '95',
      type: LocaleKeys.landingPropertyFamilies,
      imageColor: Color(0xFFFDE68A),
      isVerified: true,
    ),
  ];

  static List<FaqItem> get faqs => [
    FaqItem(LocaleKeys.landingFaqOneQuestion, LocaleKeys.landingFaqOneAnswer),
    FaqItem(LocaleKeys.landingFaqTwoQuestion, LocaleKeys.landingFaqTwoAnswer),
    FaqItem(
      LocaleKeys.landingFaqThreeQuestion,
      LocaleKeys.landingFaqThreeAnswer,
    ),
    FaqItem(LocaleKeys.landingFaqFourQuestion, LocaleKeys.landingFaqFourAnswer),
    FaqItem(LocaleKeys.landingFaqFiveQuestion, LocaleKeys.landingFaqFiveAnswer),
    FaqItem(LocaleKeys.landingFaqSixQuestion, LocaleKeys.landingFaqSixAnswer),
    FaqItem(
      LocaleKeys.landingFaqSevenQuestion,
      LocaleKeys.landingFaqSevenAnswer,
    ),
    FaqItem(
      LocaleKeys.landingFaqEightQuestion,
      LocaleKeys.landingFaqEightAnswer,
    ),
  ];

  static List<({IconData icon, String title, String subtitle, Color color})>
  get trustItems => [
    (
      icon: Icons.verified_user_outlined,
      title: LocaleKeys.landingTrustVerifiedAccountsTitle,
      subtitle: LocaleKeys.landingTrustVerifiedAccountsBody,
      color: LandingColors.teal,
    ),
    (
      icon: Icons.visibility_off_outlined,
      title: LocaleKeys.landingTrustHiddenNumbersTitle,
      subtitle: LocaleKeys.landingTrustHiddenNumbersBody,
      color: LandingColors.blue,
    ),
    (
      icon: Icons.home_work_outlined,
      title: LocaleKeys.landingTrustReviewedPropertiesTitle,
      subtitle: LocaleKeys.landingTrustReviewedPropertiesBody,
      color: LandingColors.gold,
    ),
    (
      icon: Icons.calendar_month_outlined,
      title: LocaleKeys.landingTrustOrganizedVisitsTitle,
      subtitle: LocaleKeys.landingTrustOrganizedVisitsBody,
      color: LandingColors.green,
    ),
  ];
}
