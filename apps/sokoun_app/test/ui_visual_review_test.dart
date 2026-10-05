import 'dart:io';
import 'dart:convert';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/welcome_screen.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat/chat_participant_title.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/report/chat_report_button.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_widgets/owner_stats_grid.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_property_card.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/features/shared/reviews/data/models/my_review.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/my_review_card.dart';
import 'package:sokoun_app/features/shared/public_pages/data/models/public_page_content.dart';
import 'package:sokoun_app/features/shared/public_pages/presentation/widgets/public_page_body.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/property_video.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_additional_details.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_pricing_page.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_photos_page.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_edit_review_sheet.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_photo_metadata.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/listing_information.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/widgets/property_rating_card.dart';
import 'helpers/home_page_test_dependencies.dart';

/// Opt-in PNG export; the same fixtures are used before and after refinement.
/// flutter test test/ui_visual_review_test.dart --dart-define=UI_REVIEW_DIR=/tmp/review
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const String output = String.fromEnvironment('UI_REVIEW_DIR');
  const bool darkReview = bool.fromEnvironment('DARK_THEME_REVIEW');
  const MethodChannel preferences = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          preferences,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    for (final channel in [
      const MethodChannel('dev.fluttercommunity.plus/connectivity'),
      const MethodChannel('dev.fluttercommunity.plus/connectivity_status'),
    ]) {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(
            channel,
            (call) async => call.method == 'check' ? ['wifi'] : null,
          );
    }
    registerHomePageTestDependencies(
      propertyFilterOptions: {
        'amenities': [
          {'value': 'wifi', 'label': 'Wi-Fi'},
        ],
      },
    );
    final FontLoader fonts = FontLoader(ConstantManager.fontFamily);
    for (final String weight in [
      'Regular',
      'Medium',
      'Bold',
      'ExtraBold',
      'Black',
    ]) {
      fonts.addFont(
        rootBundle.load(
          'packages/melos_core/assets/fonts/Tajawal/Tajawal-$weight.ttf',
        ),
      );
    }
    await fonts.load();
    await (FontLoader(
      'MaterialIcons',
    )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
  });

  for (final String locale in ['ar', 'en']) {
    for (final double width in [390.0, 1024.0]) {
      for (final String subject in [
        'welcome',
        'discovery',
        'dashboard',
        'language',
        'chat_header',
        'my_review',
        'public_page',
        'property_video',
        'property_metadata',
        'property_terms',
        'property_pricing',
        'property_photos',
        'property_edit_review',
        'property_listing_information',
        'property_rating',
        'property_rating_empty',
      ]) {
        testWidgets('$subject $locale at $width', (tester) async {
          tester.view.physicalSize = Size(width, width > 600 ? 768 : 844);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.reset);
          final String caption = locale == 'ar'
              ? 'غرفة المعيشة'
              : 'Living room';
          final String description = locale == 'ar'
              ? 'غرفة واسعة بإضاءة طبيعية تطل على الحديقة.'
              : 'A spacious room with natural light overlooking the garden.';
          final listing = TenantPropertyDetailsContent.fromModel(
            PropertyDetailsModel.fromJson({
              'country': locale == 'ar' ? 'مصر' : 'Egypt',
              'city': {'name': locale == 'ar' ? 'المعادي' : 'Maadi'},
              'governorate': {'name': locale == 'ar' ? 'القاهرة' : 'Cairo'},
              'district': locale == 'ar' ? 'دجلة' : 'Degla',
              'street': locale == 'ar' ? 'شارع ٢٠٠' : 'Street 200',
              'space': '120',
              'status': 'approved',
              'created_at': '2026-10-01T10:00:00Z',
              'updated_at': '2026-10-05T12:00:00Z',
              'images': [
                {
                  'image': 'https://example.com/room.jpg',
                  'name': caption,
                  'description': description,
                },
              ],
            }),
          );
          final priceController = TextEditingController(text: '6500.50');
          final rentalController = TextEditingController(text: '6');
          final descriptionController = TextEditingController(
            text: description,
          );
          addTearDown(priceController.dispose);
          addTearDown(rentalController.dispose);
          addTearDown(descriptionController.dispose);
          final Widget screen = switch (subject) {
            'property_photos' => AppScaffold(
              title: locale == 'ar' ? 'صور العقار' : 'Property photos',
              body: AddPropertyPhotosPage(
                form: OwnerAddPropertyFormState.initial(),
                photos: [
                  for (var index = 0; index < 10; index++)
                    OwnerPropertyPhotoDraft(
                      existingId: 'photo-$index',
                      existingUrl: 'https://example.com/room-$index.jpg',
                      name: caption,
                      description: description,
                    ),
                ],
                isReady: false,
                onAddPhotos: () {},
                onRemovePhoto: (_) {},
                onReplacePhoto: (_) {},
                onMainPhotoSelected: (_) {},
                onPhotoNameChanged: (_, _) {},
                onPhotoDescriptionChanged: (_, _) {},
                onVideoSelected: (_, _) {},
                onVideoRemoved: () {},
                onVideoPreparingChanged: (_) {},
                onNext: () {},
              ),
            ),
            'property_pricing' => AppScaffold(
              title: locale == 'ar'
                  ? 'التسعير والوصف'
                  : 'Pricing and description',
              body: AddPropertyPricingPage(
                form: OwnerAddPropertyFormState.initial().copyWith(
                  monthlyPrice: '6500.50',
                  rentalDuration: '6',
                  rentalUnit: 'weekly',
                  suitableFor: 'female_students',
                  description: description,
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
            'property_metadata' => AppScaffold(
              title: locale == 'ar' ? 'صور العقار' : 'Property photos',
              body: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: PhotoMetadataSection(
                  photos: [
                    OwnerPropertyPhotoDraft(
                      existingId: 'room',
                      existingUrl: 'https://example.com/room.jpg',
                      name: caption,
                      description: description,
                    ),
                  ],
                  onPhotoNameChanged: (_, _) {},
                  onPhotoDescriptionChanged: (_, _) {},
                ),
              ),
            ),
            'property_terms' => AppScaffold(
              title: locale == 'ar' ? 'تفاصيل العقار' : 'Property details',
              body: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: AddPropertyAdditionalDetails(
                  form: OwnerAddPropertyFormState.initial().copyWith(
                    country: listing.country,
                    neighborhood: listing.district,
                    buildingYear: '2020',
                    deposit: 'one_month',
                    smokingAllowed: false,
                    ownershipProofUrl: 'https://example.com/proof.jpg',
                  ),
                  onDetailsChanged: (_) {},
                ),
              ),
            ),
            'property_edit_review' => const AppScaffold(
              showBackButton: false,
              body: PropertyEditReviewSheet(),
            ),
            'property_listing_information' => AppScaffold(
              title: locale == 'ar' ? 'معلومات الإعلان' : 'Listing information',
              body: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: TenantPropertyListingInformation(property: listing),
              ),
            ),
            'property_rating' || 'property_rating_empty' => AppScaffold(
              title: locale == 'ar' ? 'تفاصيل العقار' : 'Property details',
              body: SingleChildScrollView(
                padding: const EdgeInsets.all(18),
                child: PropertyRatingCard(
                  propertyId: 'property',
                  averageRating: subject == 'property_rating' ? 4.6 : null,
                  totalReviews: subject == 'property_rating' ? 19 : 0,
                ),
              ),
            ),
            'my_review' => AppScaffold(
              title: locale == 'ar' ? 'تقييماتي' : 'My Reviews',
              body: SingleChildScrollView(
                child: MyReviewCard(
                  review: const MyReview.initial().copyWith(
                    propertyTitle: locale == 'ar'
                        ? 'شقة واسعة في المعادي'
                        : 'Spacious apartment in Maadi',
                    comment: locale == 'ar'
                        ? 'العقار مطابق للوصف والزيارة كانت منظمة.'
                        : 'The property matched the description and the visit was well organized.',
                    rating: 5,
                    createdAt: '2026-09-28T14:13:00Z',
                  ),
                ),
              ),
            ),
            'public_page' => AppScaffold(
              title: locale == 'ar' ? 'عن سكون' : 'About Sokoun',
              body: PublicPageBody(
                page: const PublicPageContent.initial().copyWith(
                  title: locale == 'ar' ? 'عن سكون' : 'About Sokoun',
                  language: locale,
                  content: locale == 'ar'
                      ? 'سكون منصة لاستكشاف العقارات وحجز الزيارات والتواصل مع الملاك.\n\nحساب واحد يتيح لك التأجير والاستئجار.'
                      : 'Sokoun helps you discover properties, book visits, and contact owners.\n\nOne account lets you rent and list properties.',
                ),
              ),
            ),
            'property_video' => AppScaffold(
              title: locale == 'ar' ? 'فيديو العقار' : 'Property video',
              body: const Padding(
                padding: EdgeInsets.all(20),
                child: PropertyVideo(
                  url: 'https://cdn.example.com/tour.mp4',
                  durationSeconds: 45,
                ),
              ),
            ),
            'welcome' => const WelcomeScreen(),
            'language' => const LanguageSelectionScreen(),
            'chat_header' => AppScaffold(
              titleWidget: ChatParticipantTitle(
                conversation: ConversationContent(
                  id: 'review-chat',
                  name: locale == 'ar' ? 'أحمد محمد' : 'Ahmed Mohamed',
                  property: locale == 'ar'
                      ? 'شقة بالمعادي'
                      : 'Apartment in Maadi',
                  lastMessage: '',
                  time: '',
                  unreadCount: 0,
                  isVerified: true,
                  isOnline: true,
                ),
              ),
              toolbarHeight: 72,
              onBack: () {},
              actions: const [ChatReportButton()],
              body: const SizedBox.expand(),
            ),
            'dashboard' => AppScaffold(
              showBackButton: false,
              contentWidth: SokounContentWidth.wide,
              body: const SingleChildScrollView(
                padding: EdgeInsets.all(20),
                child: OwnerStatsGrid(
                  visitsThisWeek: 12,
                  activeProperties: 8,
                  overallRating: 4.8,
                  pendingRequests: 3,
                ),
              ),
            ),
            _ => AppScaffold(
              showBackButton: false,
              contentWidth: SokounContentWidth.wide,
              body: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: SokounAdaptiveGrid(
                  children: [
                    for (int i = 0; i < 3; i++)
                      TenantPropertyCard(
                        title: locale == 'ar'
                            ? 'شقة واسعة بإضاءة طبيعية في المعادي'
                            : 'Bright apartment in Maadi',
                        rating: '4.8',
                        area: locale == 'ar' ? '١٢٠ م²' : '120 m²',
                        price: locale == 'ar'
                            ? '١٨٬٠٠٠ ج.م / شهر'
                            : '18,000 EGP / month',
                        icon: Icons.apartment_rounded,
                      ),
                  ],
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
              assetLoader: const _ReviewTranslations(),
              child: ScreenUtilInit(
                designSize: const Size(360, 690),
                enableScaleWH: () => false,
                enableScaleText: () => false,
                fontSizeResolver: (size, _) => size.toDouble(),
                builder: (context, _) => MaterialApp(
                  theme: darkReview ? SokounTheme.dark : SokounTheme.light,
                  locale: context.locale,
                  supportedLocales: context.supportedLocales,
                  localizationsDelegates: context.localizationDelegates,
                  home: RepaintBoundary(child: screen),
                ),
              ),
            ),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          if (output.isNotEmpty) {
            final RenderRepaintBoundary boundary = tester.renderObject(
              find.byType(RepaintBoundary).first,
            );
            await tester.runAsync(() async {
              final ui.Image image = await boundary.toImage();
              final bytes = await image.toByteData(
                format: ui.ImageByteFormat.png,
              );
              await Directory(output).create(recursive: true);
              await File(
                '$output/${darkReview ? 'dark-' : ''}$subject-$locale-${width.toInt()}.png',
              ).writeAsBytes(bytes!.buffer.asUint8List());
              image.dispose();
            });
          }
        });
      }
    }
  }
}

class _ReviewTranslations extends AssetLoader {
  const _ReviewTranslations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/${locale.languageCode}.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}
