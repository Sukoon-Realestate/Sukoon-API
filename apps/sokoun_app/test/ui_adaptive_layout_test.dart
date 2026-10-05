import 'package:sokoun_app/features/main_view/presentation/models/home_navigation_destination.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_review_sheet.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'dart:convert';
import 'dart:io';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/welcome_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/kyc_upload_documents_screen.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search_results/search_result_card.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/details_body.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_widgets/owner_stats_grid.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_photos_page.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_additional_details.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_pricing_page.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_edit_review_sheet.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_photo_metadata.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/property_rating_card.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_card.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notifications_read_action.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/chat/data/models/conversation_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_card.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/home_bottom_navigation.dart';
import 'helpers/home_page_test_dependencies.dart';
import 'package:sokoun_app/features/shared/reviews/data/models/my_review.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/my_review_card.dart';
import 'package:sokoun_app/features/shared/public_pages/data/models/public_page_content.dart';
import 'package:sokoun_app/features/shared/public_pages/presentation/widgets/public_page_body.dart';
import 'package:sokoun_app/features/shared/public_pages/presentation/widgets/public_page_menu.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('dev.fluttercommunity.plus/connectivity'),
          (_) async => ['wifi'],
        );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('dev.fluttercommunity.plus/connectivity_status'),
          (_) async => null,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    registerHomePageTestDependencies(
      propertyFilterOptions: {
        'amenities': [
          {'value': 'wifi', 'label': 'Wi-Fi'},
          {'value': 'electricity_meter', 'label': 'Electricity meter'},
        ],
      },
    );
  });
  for (final double width in [320, 390, 600, 768, 1024, 1366]) {
    for (final double scale in [1, 1.3, 2]) {
      for (final String locale in ['ar', 'en']) {
        for (final String subject in [
          'home',
          'welcome',
          'login',
          'kyc',
          'kyc_completion',
          'my_review',
          'public_page',
          'public_menu',
          'properties',
          'details',
          'dashboard',
          'photos',
          'property_review',
          'property_terms',
          'property_pricing',
          'photo_metadata',
          'property_rating',
          'property_rating_empty',
          'property_edit_review',
          'property_delete',
          'booking',
          'availability',
          'profile',
          'notifications',
          'chat',
          'navigation',
        ]) {
          testWidgets('$subject $locale width=$width text=$scale', (
            tester,
          ) async {
            tester.view.physicalSize = Size(width, width > 900 ? 768 : 844);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            final controller = TextEditingController();
            addTearDown(controller.dispose);
            final priceController = TextEditingController(text: '18500.50');
            final rentalController = TextEditingController(text: '6');
            final descriptionController = TextEditingController();
            addTearDown(priceController.dispose);
            addTearDown(rentalController.dispose);
            addTearDown(descriptionController.dispose);
            final String title = locale == 'ar'
                ? 'شقة واسعة بإضاءة طبيعية في منطقة هادئة بالمعادي'
                : 'Bright spacious apartment in a quiet Maadi neighborhood';
            final property = PropertyDetailsModel.fromJson({
              'id': 'review-property',
              'title': title,
              'description': '$title. $title.',
              'price': '18500',
              'area': 120,
              'bedrooms': 3,
              'bathrooms': 2,
              'images': [],
              'video': 'https://cdn.example.com/tour.mp4',
              'video_duration': 45,
              'country': 'Egypt',
              'governorate': {
                'id': 'cairo',
                'name': locale == 'ar' ? 'القاهرة' : 'Cairo',
              },
              'city': {
                'id': 'maadi',
                'name': locale == 'ar' ? 'المعادي' : 'Maadi',
              },
              'district': title,
              'street': title,
              'space': '120',
              'deposit': 'one_month',
              'building_year': 2020,
              'smoking_allowed': false,
              'status': 'under_review',
              'created_at': '2026-10-01T10:00:00Z',
              'updated_at': '2026-10-05T12:00:00Z',
            });
            Widget scroll(Widget child) => AppScaffold(
              showBackButton: false,
              contentWidth: SokounContentWidth.wide,
              body: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: child,
              ),
            );
            Widget page(Widget child) => AppScaffold(
              showBackButton: false,
              body: SafeArea(child: child),
            );
            final Widget screen = switch (subject) {
              'home' => const TenantHomeScreen(),
              'welcome' => const WelcomeScreen(),
              'login' => const LoginScreen(),
              'kyc' => const KycUploadDocumentsScreen(),
              'kyc_completion' => const KycUploadDocumentsScreen(
                existingAccount: true,
              ),
              'my_review' => scroll(
                MyReviewCard(
                  review: const MyReview.initial().copyWith(
                    propertyTitle: title,
                    comment: '$title. $title.',
                    rating: 5,
                    createdAt: '2026-09-28T14:13:00Z',
                  ),
                ),
              ),
              'public_page' => page(
                PublicPageBody(
                  page: const PublicPageContent.initial().copyWith(
                    title: title,
                    content: List.filled(10, title).join('\n\n'),
                    language: locale,
                  ),
                ),
              ),
              'public_menu' => scroll(const PublicPageMenu()),
              'properties' => scroll(
                SokounAdaptiveGrid(
                  children: [
                    SearchResultCard(
                      item: property,
                      filterOptions: const PropertyFilterOptionsModel.initial(),
                    ),
                  ],
                ),
              ),
              'details' => AppScaffold(
                showBackButton: false,
                contentWidth: SokounContentWidth.wide,
                body: TenantPropertyDetailsBody(
                  property: TenantPropertyDetailsContent.fromModel(property),
                  isSaved: false,
                  onSavedPressed: () {},
                ),
              ),
              'dashboard' => scroll(
                const OwnerStatsGrid(
                  visitsThisWeek: 12,
                  activeProperties: 8,
                  overallRating: 4.8,
                  pendingRequests: 3,
                ),
              ),
              'photos' => page(
                AddPropertyPhotosPage(
                  form: OwnerAddPropertyFormState.initial(),
                  photos: const [],
                  isReady: false,
                  onAddPhotos: () {},
                  onRemovePhoto: (_) {},
                  onReplacePhoto: (_) {},
                  onMainPhotoSelected: (_) {},
                  onVideoSelected: (_, _) {},
                  onVideoRemoved: () {},
                  onVideoPreparingChanged: (_) {},
                  onPhotoNameChanged: (_, _) {},
                  onPhotoDescriptionChanged: (_, _) {},
                  onNext: () {},
                ),
              ),
              'property_review' => page(
                PropertyReviewSheet(
                  form: OwnerAddPropertyFormState.initial().copyWith(
                    title: title,
                    description: title,
                  ),
                  isEditing: false,
                ),
              ),
              'property_pricing' => page(
                AddPropertyPricingPage(
                  form: OwnerAddPropertyFormState.initial().copyWith(
                    monthlyPrice: '18500.50',
                    rentalDuration: '6',
                    rentalUnit: 'weekly',
                    suitableFor: 'female_students',
                    description: '$title. $title.',
                    amenities: {'wifi'},
                  ),
                  monthlyPriceController: priceController,
                  rentalDurationController: rentalController,
                  descriptionController: descriptionController,
                  onMonthlyPriceChanged: (_) {},
                  onSuitableForSelected: (_) {},
                  onRentalDurationChanged: (_) {},
                  onRentalUnitChanged: (_) {},
                  onAmenityToggled: (_) {},
                  onDescriptionChanged: (_) {},
                  onAdditionalDetailsChanged: (_) {},
                  onNext: () {},
                ),
              ),
              'property_terms' => scroll(
                AddPropertyAdditionalDetails(
                  form: OwnerAddPropertyFormState.initial().copyWith(
                    country: 'Egypt',
                    neighborhood: title,
                    buildingYear: '2020',
                    deposit: 'one_month',
                    smokingAllowed: false,
                    ownershipProofUrl: 'https://example.com/proof.jpg',
                  ),
                  onDetailsChanged: (_) {},
                ),
              ),
              'photo_metadata' => scroll(
                PhotoMetadataSection(
                  photos: [
                    OwnerPropertyPhotoDraft(
                      existingId: 'photo',
                      existingUrl: 'https://example.com/room.jpg',
                      name: title,
                      description: title,
                    ),
                  ],
                  onPhotoNameChanged: (_, _) {},
                  onPhotoDescriptionChanged: (_, _) {},
                ),
              ),
              'property_rating' || 'property_rating_empty' => scroll(
                PropertyRatingCard(
                  propertyId: 'property',
                  averageRating: subject == 'property_rating' ? 4.6 : null,
                  totalReviews: subject == 'property_rating' ? 123456 : 0,
                ),
              ),
              'property_edit_review' => page(const PropertyEditReviewSheet()),
              'property_delete' => page(
                OwnerPropertyDeleteSheet(
                  property: OwnerPropertyContent.initial().copyWith(
                    id: 'property',
                    title: title,
                  ),
                ),
              ),
              'booking' => page(
                BookVisitForm(
                  property: VisitPropertyContent(title: title, meta: title),
                  days: const [
                    VisitDayContent(
                      weekday: 'Tuesday',
                      day: '29',
                      month: '9',
                      visitDate: '2026-09-29',
                    ),
                  ],
                  selectedDayIndex: 0,
                  selectedTime: const TimeOfDay(hour: 10, minute: 30),
                  noteController: controller,
                  onDaySelected: (_) {},
                  onTimeSelected: (_) {},
                  onConfirmPressed: (_) async {},
                ),
              ),
              'availability' => page(
                OwnerAvailabilityContent(
                  days: [
                    OwnerAvailabilityDayContent.fromDate(DateTime(2026, 9, 29)),
                  ],
                  slots: const [
                    OwnerAvailabilitySlotBody(time: '10:30', isEnabled: true),
                  ],
                  slotStates: const [OwnerAvailabilitySlotState.available],
                  selectedDayIndex: 0,
                  onDaySelected: (_) {},
                  onTimePressed: (_) {},
                  onSavePressed: () async {},
                ),
              ),
              'profile' => scroll(
                TenantProfileHeaderCard(
                  profile: AccountContent.fromJson({
                    'user': {'full_name': title},
                    'stats': {'saved_count': 12},
                  }),
                  onEditPressed: () {},
                ),
              ),
              'notifications' => scroll(
                Column(
                  children: [
                    NotificationsReadAction(
                      role: NotificationRole.tenant,
                      hasUnread: true,
                      isMarkingAll: false,
                      onMarkAllPressed: () {},
                    ),
                    NotificationCard(
                      notification: AppNotificationContent.fromJson({
                        'id': '1',
                        'title': title,
                        'body': '$title. $title.',
                        'is_read': false,
                      }),
                      onPressed: () {},
                    ),
                  ],
                ),
              ),
              'chat' => scroll(
                ChatCard(
                  conversation: ConversationContent(
                    id: '1',
                    name: title,
                    property: title,
                    lastMessage: title,
                    time: '10:30',
                    unreadCount: 12,
                    isVerified: true,
                    isOnline: true,
                  ),
                ),
              ),
              _ => page(
                Align(
                  alignment: Alignment.bottomCenter,
                  child: HomeBottomNavigation(
                    destinations: [
                      for (final String label
                          in locale == 'ar'
                              ? [
                                  'الرئيسية',
                                  'المحفوظات',
                                  'الرسائل',
                                  'الزيارات',
                                  'حسابي',
                                ]
                              : [
                                  'Home',
                                  'Saved',
                                  'Messages',
                                  'Visits',
                                  'Account',
                                ])
                        HomeNavigationDestination(
                          icon: Icons.home_outlined,
                          selectedIcon: Icons.home,
                          label: label,
                          badgeCount: 120,
                        ),
                    ],
                    currentIndex: 0,
                    onDestinationSelected: (_) {},
                  ),
                ),
              ),
            };
            await tester.pumpWidget(
              EasyLocalization(
                supportedLocales: Languages.supportedLocales,
                path: Languages.translationsPath,
                startLocale: Locale(locale),
                saveLocale: false,
                assetLoader: const _Translations(),
                child: ScreenUtilInit(
                  designSize: const Size(360, 690),
                  enableScaleWH: () => false,
                  enableScaleText: () => false,
                  fontSizeResolver: (size, _) => size.toDouble(),
                  builder: (context, _) => MaterialApp(
                    theme: SokounTheme.light,
                    locale: context.locale,
                    supportedLocales: context.supportedLocales,
                    localizationsDelegates: context.localizationDelegates,
                    home: MediaQuery(
                      data: MediaQuery.of(context).copyWith(
                        textScaler: TextScaler.linear(scale),
                        disableAnimations: true,
                      ),
                      child: screen,
                    ),
                  ),
                ),
              ),
            );
            await tester.pumpAndSettle();
            expect(tester.takeException(), isNull);
            await tester.pumpWidget(const SizedBox.shrink());
          });
        }
      }
    }
  }
}

class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    final file = [
      File(
        '../../packages/core/assets/translations/${locale.languageCode}.json',
      ),
      File('packages/core/assets/translations/${locale.languageCode}.json'),
    ].firstWhere((f) => f.existsSync());
    return jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
  }
}
