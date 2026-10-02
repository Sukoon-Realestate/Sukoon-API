import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/imports.dart';
import 'package:sokoun_app/shared_widgets/property_details_screen.dart';
import 'helpers/account_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _PropertyDetailsRepository repository;

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
  });

  setUp(() async {
    await injector.reset();
    repository = _PropertyDetailsRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
    await CacheStorage.write('user', const <String, dynamic>{
      'id': 1,
      'name': 'Tenant Test User',
      'email': 'tenant@example.com',
      'type': 'tenant',
    });
    await registerAuthenticatedTestAccount();
  });

  tearDown(() async {
    await CacheStorage.delete('user');
    await injector.reset();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  Widget buildScreen() {
    return EasyLocalization(
      supportedLocales: const [Locale('ar')],
      path: 'unused',
      assetLoader: const _PropertyDetailsAssetLoader(),
      startLocale: const Locale('ar'),
      fallbackLocale: const Locale('ar'),
      child: ScreenUtilInit(
        designSize: Size(ScreenSizes.width, ScreenSizes.height),
        builder: (context, _) {
          return MaterialApp(
            navigatorKey: Go.navigatorKey,
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            locale: context.locale,
            home: const PropertyDetailsScreen(propertyId: 'property-id'),
          );
        },
      ),
    );
  }

  testWidgets('composes details and handles local actions', (tester) async {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(buildScreen());
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.byType(TenantPropertyDetailsBody), findsOneWidget);
    expect(find.byType(TenantPropertyDetailsContentView), findsOneWidget);
    expect(find.byIcon(Icons.bookmark_border_rounded), findsOneWidget);
    expect(repository.detailsCacheKey, 'property_details_property-id');
    expect(repository.hasCacheDeserializer, isTrue);
    expect(repository.hasCacheSerializer, isTrue);
    expect(tester.takeException(), isNull);

    final Widget gallery = tester.widget(
      find.byType(TenantPropertyHeroGallery),
    );
    final Widget details = tester.widget(
      find.byType(TenantPropertyDetailsContentView),
    );
    await tester.tap(find.byIcon(Icons.bookmark_border_rounded));
    await tester.pump();

    expect(find.byIcon(Icons.bookmark_rounded), findsOneWidget);
    expect(
      tester.widget(find.byType(TenantPropertyHeroGallery)),
      same(gallery),
    );
    expect(
      tester.widget(find.byType(TenantPropertyDetailsContentView)),
      same(details),
    );

    await tester.tap(find.byIcon(Icons.ios_share_rounded));
    await tester.pumpAndSettle();

    expect(find.byType(TenantPropertyShareSheet), findsOneWidget);
    expect(find.text('مشاركة العقار'), findsOneWidget);

    await tester.tap(find.text('إلغاء'));
    await tester.pumpAndSettle();

    expect(find.byType(TenantPropertyShareSheet), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('shows the exception view when no cached details exist', (
    tester,
  ) async {
    repository.failDetailsRequest = true;
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(buildScreen());
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));

    expect(find.byType(AppBar), findsOneWidget);
    expect(find.byType(ExceptionView), findsOneWidget);
    expect(find.byType(TenantPropertyDetailsBody), findsNothing);
    await tester.pump(const Duration(seconds: 5));
  });
}

class _PropertyDetailsRepository implements BaseRepository {
  bool failDetailsRequest = false;
  String? detailsCacheKey;
  bool hasCacheDeserializer = false;
  bool hasCacheSerializer = false;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    if (params.api.endsWith('/reviews/')) {
      final T summary = params.mapper!(const {
        'summary': {'total_reviews': 7, 'average_rating': 4.2},
      });
      return Success(BaseModel<T>(key: '', msg: '', data: summary));
    }
    if (params.httpRequestType == HttpRequestType.get) {
      if (failDetailsRequest) {
        return const Error(Failure('offline'));
      }
      detailsCacheKey = params.cacheKey;
      hasCacheDeserializer = params.fromCacheJson != null;
      hasCacheSerializer = params.toJson != null;
      final T data = params.mapper!(const {
        'id': 'property-id',
        'owner': 'أحمد محمد إبراهيم',
        'title': 'شقة مفروشة 3 غرف',
        'property_type': 'apartment',
        'district': 'مدينة نصر',
        'city': {'name': 'القاهرة'},
        'price': '6500',
        'is_furnished': true,
        'is_saved': false,
      });
      final Map<String, dynamic> cachedJson = params.toJson!(data);
      final T restoredData = params.fromCacheJson!(cachedJson);
      return Success(BaseModel<T>(key: '', msg: '', data: restoredData));
    }

    final T data = params.mapper!(null);
    return Success(BaseModel<T>(key: '', msg: '', data: data));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _PropertyDetailsAssetLoader extends AssetLoader {
  const _PropertyDetailsAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      'cancel': 'إلغاء',
      'verified': 'موثّق',
      'tenant_visit_book_title': 'احجز زيارة',
      'tenant_property_details_share_title': 'مشاركة العقار',
      'tenant_property_details_copy_link': 'نسخ الرابط',
      'tenant_property_details_link_copied': 'تم نسخ الرابط',
      'tenant_property_details_share': 'مشاركة',
      'tenant_property_details_description': 'الوصف',
      'tenant_property_details_amenities': 'المرافق',
      'tenant_property_details_ownership_verified':
          'تم التحقق من إثبات الملكية',
      'tenant_property_details_phone_privacy':
          'رقم الموبايل مخفي ومش هيظهر غير بموافقة واضحة',
      'tenant_property_details_furnished': 'مفروشة',
      'tenant_property_details_monthly_price_unit': 'ج / شهر',
      'tenant_property_details_photo_count_unit': 'صورة',
      'tenant_property_details_photos': 'صور',
    };
  }
}
