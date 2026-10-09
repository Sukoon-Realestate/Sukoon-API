import 'package:melos_core/core/helpers/cache_service.dart';
import 'helpers/account_test_dependencies.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/data/base_data_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/dio_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_tenant_type.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/models/property_location.dart';
import 'package:sokoun_app/features/owner/home/data/models/property_upload_progress.dart';
import 'package:sokoun_app/features/owner/home/data/owner_add_property_mapper.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/property_submission_cubit.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/upload_property_images_cubit.dart';
import 'package:sokoun_app/features/owner/properties/presentation/cubits/delete_owner_property_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _HandoffRepository repository;

  setUpAll(CacheStorage.init);

  setUp(() async {
    await injector.reset();
    await registerAuthenticatedTestAccount();
    repository = _HandoffRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
  });
  tearDown(() => injector.reset());

  for (final status in [
    PropertyUploadStatus.sending,
    PropertyUploadStatus.unknown,
  ]) {
    testWidgets(
      'removing a $status photo cannot silently complete an upload session',
      (tester) async {
        await tester.pumpWidget(
          ScreenUtilInit(
            designSize: const Size(360, 690),
            builder: (_, __) => MaterialApp(
              navigatorKey: Go.navigatorKey,
              home: const Scaffold(),
            ),
          ),
        );
        await tester.pumpAndSettle();
        final cubit = UploadPropertyImagesCubit();
        addTearDown(cubit.close);
        bool completed = false;
        await cubit.uploadImages(
          propertyId: 'property-id',
          photos: _readyForm().photoDrafts,
          restoredUploads: {
            'removed-photo': PropertyUploadProgress(
              reference: 'removed-photo',
              status: status,
            ),
          },
          onPhotoUploaded: ({required photo, required image}) {},
          onSuccess: () => completed = true,
        );
        expect(repository.requests, isEmpty);
        expect(completed, isFalse);
        expect(cubit.state.isError, isTrue);
        expect(cubit.uploads['removed-photo']?.status, status);
        await tester.pump(const Duration(seconds: 5));
        await tester.pumpAndSettle();
      },
    );
  }

  test('the backend handoff response survives caching and reaches details', () {
    final json = _handoffProperty();
    final property = PropertyDetailsModel.fromJson(json);
    final cached = PropertyDetailsModel.fromJson(property.toJson());
    final content = TenantPropertyDetailsContent.fromModel(cached);

    expect(cached, property);
    expect(content.ownerName, 'Ahmed Mohamed');
    expect(content.ownerId, (json['owner'] as Map)['id']);
    expect(content.ownerAvatar, (json['owner'] as Map)['avatar']);
    expect(content.isOwnerVerified, isTrue);
    expect(content.isOwnershipVerified, isFalse);
    expect(content.imageUrls, hasLength(2));
    expect(content.imageUrls.first, json['main_image']);
    expect(content.photoLabels, ['Living room', 'Master bedroom']);
    expect(content.photoDescriptions, ['Natural light throughout the day', '']);
    expect(content.videoUrl, json['video']);
    expect(content.videoDuration, 35);
    expect(content.propertyLink, json['property_link']);
    expect(content.governorateName, 'Cairo');
    expect(content.cityName, 'Nasr City');
    expect(content.district, json['district']);
    expect(content.street, json['street']);
    expect(content.status, 'under_review');
    expect(content.createdAt, json['created_at']);
    expect(content.updatedAt, json['updated_at']);
    expect(property.ownershipProof, isNotEmpty);
    expect(
      PropertyDetailsModel.fromJson({
        ...json,
        'ownership_proof': null,
      }).ownershipProof,
      isEmpty,
    );
    expect(property.copyWith(ownerAvatar: '').ownerAvatar, isEmpty);
  });

  test('cover-first responses seed unique photos and stable image IDs', () {
    final property = PropertyDetailsModel.fromJson(_handoffProperty());
    final seed = OwnerAddPropertyMapper.fromProperty(property).form;
    expect(seed.photoDrafts, hasLength(2));
    expect(seed.photoDrafts.first.existingId, property.mainImageId);
    expect(seed.photoDrafts.first.name, property.mainImageName);
    expect(seed.photoDrafts.first.description, property.mainImageDescription);
    expect(_readyForm().isPhotosReady, isTrue);
  });

  test(
    'request coordinates use six decimals without changing the map location',
    () {
      for (final coordinates in [
        (
          location: const PropertyLocation(
            latitude: 30.044456789,
            longitude: -31.235765432,
          ),
          latitude: '30.044457',
          longitude: '-31.235765',
        ),
        (
          location: const PropertyLocation(
            latitude: -0.00000011,
            longitude: 179.99999999,
          ),
          latitude: '-0.000000',
          longitude: '180.000000',
        ),
      ]) {
        final form = _readyForm().copyWith(location: coordinates.location);
        for (final isEditing in [false, true]) {
          final body = form.toJson(isEditing: isEditing);
          expect(body['latitude'], coordinates.latitude);
          expect(body['longitude'], coordinates.longitude);
        }
        expect(form.location, coordinates.location);
        expect(
          form.location!.toJson()['latitude'],
          coordinates.location.latitude,
        );
        expect(
          form.location!.toJson()['longitude'],
          coordinates.location.longitude,
        );
      }
    },
  );

  for (final isEditing in [false, true]) {
    test(
      '${isEditing ? 'PATCH' : 'POST'} uploads video bytes and six-decimal coordinates through Dio',
      () async {
        final directory = Directory.systemTemp.createTempSync(
          'property-upload-',
        );
        addTearDown(() => directory.deleteSync(recursive: true));
        final video = File('${directory.path}/tour.mp4')
          ..writeAsBytesSync(utf8.encode('video upload bytes'));
        final cover = File('${directory.path}/cover.jpg')
          ..writeAsBytesSync(utf8.encode('cover upload bytes'));
        final response = _handoffProperty();
        final adapter = _PropertyUploadAdapter(response);
        final network = DioService(
          initialBaseUrl: 'https://api.example.com/api/v1/',
          initialLanguageCode: 'en',
          cookieDirectoryProvider: () async => directory,
          httpClientAdapter: adapter,
        );
        await injector.unregister<BaseCrudUseCase>();
        injector.registerSingleton<BaseCrudUseCase>(
          BaseCrudUseCase(
            repository: BaseRepositoryImpl(
              baseRemoteDataSource: BaseRemoteDataSourceImpl(
                dioService: network,
              ),
              baseLocalDataSource: BaseLocalDataSourceImpl(),
            ),
          ),
        );
        final seed = _readyForm();
        final form = seed.copyWith(
          location: const PropertyLocation(
            latitude: 30.044456789,
            longitude: 31.235765432,
          ),
          photoDrafts: [
            OwnerPropertyPhotoDraft(file: cover),
            ...seed.photoDrafts.skip(1),
          ],
          videoFile: video,
          videoDuration: 35,
          removeVideo: false,
        );
        final cubit = PropertySubmissionCubit();
        addTearDown(cubit.close);
        PropertyDetailsModel? saved;
        await cubit.save(
          form: form,
          propertyId: isEditing ? response['id'] as String : null,
          onSuccess: (property) => saved = property,
        );

        expect(adapter.request!.method, isEditing ? 'PATCH' : 'POST');
        expect(
          adapter.request!.uri.path,
          isEditing
              ? '/api/v1/properties/${response['id']}/'
              : '/api/v1/properties/create/',
        );
        expect(
          adapter.request!.contentType,
          startsWith('multipart/form-data; boundary='),
        );
        expect(adapter.request!.sendTimeout, ConstantManager.uploadSendTimeout);
        final fields = Map.fromEntries(
          (adapter.request!.data as FormData).fields,
        );
        expect(fields['latitude'], '30.044457');
        expect(fields['longitude'], '31.235765');
        expect(fields['video_duration'], '35');
        expect(fields.containsKey('remove_video'), isFalse);
        final file = (adapter.request!.data as FormData).files
            .singleWhere((file) => file.key == 'video')
            .value;
        expect(file.filename, 'tour.mp4');
        expect(file.contentType.toString(), 'video/mp4');
        expect(adapter.body, contains('name="latitude"\r\n\r\n30.044457\r\n'));
        expect(adapter.body, contains('name="longitude"\r\n\r\n31.235765\r\n'));
        expect(adapter.body, contains('name="video"; filename="tour.mp4"'));
        expect(adapter.body, contains('\r\n\r\nvideo upload bytes\r\n'));
        expect(
          adapter.body,
          contains('name="main_image"; filename="cover.jpg"'),
        );
        expect(saved?.video, response['video']);
        expect(saved?.videoDuration, 35);
      },
    );
  }

  test(
    'area and its optional display description are independent and editable',
    () {
      final property = PropertyDetailsModel.fromJson({
        ..._handoffProperty(),
        'space': '120 m² of usable space',
      });
      final form = OwnerAddPropertyMapper.fromProperty(property).form;
      expect(form.space, '120');
      expect(form.areaDescription, '120 m² of usable space');
      expect(form.isBasicsReady, isTrue);
      expect(form.toJson(isEditing: true)['area'], 120);
      expect(form.toJson(isEditing: true)['space'], property.space);
      expect(
        form.copyWith(areaDescription: '').toJson(isEditing: true)['space'],
        '',
      );
    },
  );

  for (final floor in ['', '0', '-1']) {
    test(
      'floor $floor is valid and sent with the documented clearing behavior',
      () {
        final form = _readyForm().copyWith(floor: floor);
        expect(form.isBasicsReady, isTrue);
        expect(
          form.toJson(isEditing: true)['floor'],
          floor.isEmpty ? '' : int.parse(floor),
        );
      },
    );
  }

  test('integer fields reject fractions before request serialization', () {
    final form = _readyForm();
    expect(form.copyWith(bedrooms: '1.5').isBasicsReady, isFalse);
    expect(form.copyWith(bathrooms: '1.5').isBasicsReady, isFalse);
    expect(form.copyWith(space: '120.5').isBasicsReady, isFalse);
    expect(form.copyWith(floor: '-1.5').isBasicsReady, isFalse);
    expect(form.copyWith(rentalDuration: '1.5').isPricingReady, isFalse);
    expect(
      form.copyWith(monthlyPrice: '6500.50', deposit: '1500.50').isPricingReady,
      isTrue,
    );
  });

  test(
    'localized numeric editing preserves signed floors and decimal amounts',
    () {
      const signed = LocalizedDigitsFormatter(allowNegative: true);
      const decimal = LocalizedDigitsFormatter(allowDecimal: true);
      const empty = TextEditingValue.empty;
      final floor = signed.formatEditUpdate(
        empty,
        const TextEditingValue(
          text: '-١',
          selection: TextSelection.collapsed(offset: 2),
        ),
      );
      expect(floor.text, '-1');
      expect(floor.selection.baseOffset, 2);
      expect(
        signed.formatEditUpdate(floor, const TextEditingValue(text: '--1')),
        floor,
      );
      expect(
        decimal
            .formatEditUpdate(empty, const TextEditingValue(text: '٦٥٠٠٫٥٠'))
            .text,
        '6500.50',
      );
      expect(
        decimal.formatEditUpdate(empty, const TextEditingValue(text: '-١')),
        empty,
      );
      expect(
        const LocalizedDigitsFormatter()
            .formatEditUpdate(empty, const TextEditingValue(text: '١۲3'))
            .text,
        '123',
      );
    },
  );

  for (final type in PropertyTenantType.values) {
    test(
      '${type.value} uses the documented slug and months independently of pricing',
      () {
        final form = _readyForm().copyWith(
          suitableFor: type.label,
          rentalUnit: 'weekly',
          rentalDuration: '6',
        );
        expect(form.isPricingReady, isTrue);
        final body = form.toJson(isEditing: true);
        expect(body['suitable_for'], type.value);
        expect(body['price_period'], 'weekly');
        expect(body['rental_period'], 6);
        expect(
          PropertyDetailsModel.fromJson({
            'price_period': 'weekly',
            'rental_period': 6,
          }).rentalPeriodUnitLabel,
          LocaleKeys.ownerAddPropertyMonth,
        );
      },
    );
  }

  for (final period in PropertyPricePeriod.values) {
    test('${period.value} retains a minimum stay in months', () {
      final form = _readyForm().copyWith(rentalUnit: period.label);
      expect(form.isPricingReady, isTrue);
      expect(form.toJson()['price_period'], period.value);
      expect(form.toJson()['rental_period'], 6);
    });
  }

  test(
    'unsupported legacy choices remain visible but cannot reach the server',
    () {
      final form = _readyForm().copyWith(amenities: {'wifi', 'swimming_pool'});
      expect(form.unsupportedAmenities, {'swimming_pool'});
      expect(form.isPricingReady, isFalse);
      expect(
        form.copyWith(amenities: {'wifi', 'furnished'}).isPricingReady,
        isTrue,
      );
      final body = form.copyWith(amenities: {'wifi', 'furnished'}).toJson();
      expect(jsonDecode(body['amenities'] as String), ['wifi']);
      expect(body['is_furnished'], isTrue);
      expect(
        form.copyWith(amenities: {}, suitableFor: 'males_only').isPricingReady,
        isFalse,
      );
    },
  );

  test(
    'PATCH retains selected IDs, promotes the cover, and clears optional terms',
    () {
      final seed = _readyForm();
      final photos = List<OwnerPropertyPhotoDraft>.of(seed.photoDrafts);
      photos.removeAt(0);
      photos[0] = photos[0].copyWith(name: '  غرفة النوم  ', description: ' ');
      final form = seed.copyWith(
        photoDrafts: photos,
        country: '',
        floor: '',
        buildingYear: '',
        deposit: '',
        clearSmokingAllowed: true,
        clearVideo: true,
        removeVideo: true,
        clearOwnershipProof: true,
        removeOwnershipProof: true,
      );
      final body = form.toJson(isEditing: true);
      expect(jsonDecode(body['retained_image_ids'] as String), [
        'bedroom-image-uuid',
      ]);
      expect(jsonDecode(body['images_metadata'] as String), [
        {'id': 'bedroom-image-uuid', 'name': 'غرفة النوم', 'description': ''},
      ]);
      expect(body['main_image_id'], 'bedroom-image-uuid');
      expect(body['main_image_name'], 'غرفة النوم');
      expect(body['main_image_description'], '');
      expect(body.containsKey('main_image'), isFalse);
      for (final field in [
        'country',
        'floor',
        'building_year',
        'deposit',
        'smoking_allowed',
      ]) {
        expect(body[field], '');
      }
      expect(body['remove_video'], isTrue);
      expect(body['remove_ownership_proof'], isTrue);
      expect(body.containsKey('video'), isFalse);
      expect(body.containsKey('ownership_proof'), isFalse);
    },
  );

  test(
    'creation sends cover, video, and ownership proof in one multipart request',
    () async {
      final cover = File('/tmp/new-cover.jpg');
      final form = _readyForm().copyWith(
        photoDrafts: List.generate(
          10,
          (index) => OwnerPropertyPhotoDraft(
            file: index == 0 ? cover : File('/tmp/photo-$index.jpg'),
          ),
        ),
        videoFile: File('/tmp/tour.mp4'),
        videoDuration: 60,
        ownershipProofFile: File('/tmp/proof.png'),
      );
      repository.response = _handoffProperty();
      final cubit = PropertySubmissionCubit();
      addTearDown(cubit.close);
      expect(repository.requests, isEmpty);
      PropertyDetailsModel? saved;
      await cubit.save(form: form, onSuccess: (property) => saved = property);
      final request = repository.requests.single;
      expect(request.api, ApiConstants.createProperty);
      expect(request.httpRequestType, HttpRequestType.post);
      expect(request.isFromData, isTrue);
      expect(request.body!['main_image'], cover);
      expect(request.body!['main_image_name'], '');
      expect(request.body!['main_image_description'], '');
      expect(request.body!['video'], form.videoFile);
      expect(request.body!['video_duration'], 60);
      expect(request.body!['ownership_proof'], form.ownershipProofFile);
      expect(saved?.price, '6500.00');
      expect(saved?.images, hasLength(2));
      expect(saved?.ownerAvatar, isNotEmpty);
    },
  );

  test(
    'editing consumes the full response including nullable removals',
    () async {
      final response = {
        ..._handoffProperty(),
        'floor': null,
        'building_year': null,
        'smoking_allowed': null,
        'ownership_proof': null,
        'price': '7123.50',
      };
      repository.response = response;
      final cubit = PropertySubmissionCubit();
      addTearDown(cubit.close);
      PropertyDetailsModel? saved;
      await cubit.save(
        propertyId: response['id'] as String,
        form: _readyForm().copyWith(
          floor: '',
          buildingYear: '',
          clearSmokingAllowed: true,
          monthlyPrice: '7123.5',
          clearOwnershipProof: true,
          removeOwnershipProof: true,
        ),
        onSuccess: (property) => saved = property,
      );
      final request = repository.requests.single;
      expect(
        request.api,
        ApiConstants.propertyDetails(response['id'] as String),
      );
      expect(request.httpRequestType, HttpRequestType.patch);
      expect(request.isFromData, isTrue);
      expect(saved, PropertyDetailsModel.fromJson(response));
      expect(saved?.floor, isNull);
      expect(saved?.video, response['video']);
      expect(saved?.ownershipProof, isEmpty);
    },
  );

  test(
    'creation requires a video upload and editing can retain an existing video',
    () async {
      repository.response = _handoffProperty();
      final cubit = PropertySubmissionCubit();
      addTearDown(cubit.close);
      await cubit.save(
        form: _readyForm(),
        onSuccess: (_) => fail('A new property cannot reuse a video URL'),
      );
      expect(repository.requests, isEmpty);
      PropertyDetailsModel? saved;
      await cubit.save(
        form: _readyForm(),
        propertyId: repository.response['id'] as String,
        onSuccess: (property) => saved = property,
      );
      expect(repository.requests.single.httpRequestType, HttpRequestType.patch);
      expect(saved?.video, repository.response['video']);
    },
  );

  test(
    'missing photos or video prevent creating and editing a property',
    () async {
      final valid = _readyForm().copyWith(
        videoFile: File('/tmp/tour.mp4'),
        videoDuration: 35,
      );
      final cubit = PropertySubmissionCubit();
      addTearDown(cubit.close);
      for (final propertyId in <String?>[null, 'existing-property']) {
        for (final form in [
          valid.copyWith(clearVideo: true),
          valid.copyWith(clearVideo: true, removeVideo: true),
          valid.copyWith(photoDrafts: []),
          valid.copyWith(photoDrafts: valid.photoDrafts.take(9).toList()),
          valid.copyWith(isVideoPreparing: true),
        ]) {
          await cubit.save(
            form: form,
            propertyId: propertyId,
            onSuccess: (_) => fail('Required media is missing'),
          );
        }
      }
      expect(repository.requests, isEmpty);
    },
  );

  test(
    'invalid durations and conflicting media removal flags block submission',
    () async {
      final form = _readyForm();
      final cubit = PropertySubmissionCubit();
      addTearDown(cubit.close);
      for (final invalid in [
        form.copyWith(clearVideo: true),
        form.copyWith(clearVideo: true, removeVideo: true),
        form.copyWith(videoFile: File('/tmp/tour.mp4'), videoDuration: 0),
        form.copyWith(videoFile: File('/tmp/tour.mp4'), videoDuration: 61),
        form.copyWith(
          videoFile: File('/tmp/tour.mp4'),
          videoDuration: 35,
          removeVideo: true,
        ),
        form.copyWith(
          ownershipProofFile: File('/tmp/proof.jpg'),
          removeOwnershipProof: true,
        ),
      ]) {
        await cubit.save(
          form: invalid,
          onSuccess: (_) => fail('Invalid media was saved'),
        );
      }
      expect(repository.requests, isEmpty);
    },
  );

  for (final invalid in [
    {'id': 'property-id', 'deleted': false},
    {'id': 'different-property', 'deleted': true},
    {'deleted': true},
  ]) {
    test(
      'deletion requires confirmation for the requested property: $invalid',
      () async {
        repository.response = invalid;
        repository.message = 'Server refused deletion';
        final cubit = DeleteOwnerPropertyCubit();
        addTearDown(cubit.close);
        await cubit.delete(
          propertyId: 'property-id',
          onSuccess: () => fail('Unconfirmed deletion'),
        );
        expect(cubit.state.isError, isTrue);
        expect(cubit.state.msg, 'Server refused deletion');
      },
    );
  }

  test(
    'deletion has no body and ignores repeated taps while awaiting confirmation',
    () async {
      repository.pending = Completer<Map<String, dynamic>>();
      final cubit = DeleteOwnerPropertyCubit();
      addTearDown(cubit.close);
      expect(repository.requests, isEmpty);
      var successCount = 0;
      final deletion = cubit.delete(
        propertyId: 'property-id',
        onSuccess: () => successCount++,
      );
      await cubit.delete(
        propertyId: 'property-id',
        onSuccess: () => successCount++,
      );
      expect(repository.requests, hasLength(1));
      final request = repository.requests.single;
      expect(request.api, 'properties/property-id/delete/');
      expect(request.httpRequestType, HttpRequestType.delete);
      expect(request.body, isNull);
      expect(successCount, 0);
      repository.pending!.complete({'id': 'property-id', 'deleted': true});
      await deletion;
      expect(successCount, 1);
      expect(cubit.state.isSuccess, isTrue);
    },
  );
}

Map<String, dynamic> _handoffProperty() {
  final source = File(
    '../../MOBILE_PROPERTY_MEDIA_EDITING_DELETION_HANDOFF.md',
  ).readAsStringSync();
  for (final match in RegExp(r'```json\s*([\s\S]*?)```').allMatches(source)) {
    final envelope = jsonDecode(match.group(1)!) as Map;
    final data = envelope['data'];
    if (data is Map && data['owner'] is Map && data['images'] is List) {
      return Map<String, dynamic>.from(data);
    }
  }
  throw StateError('The handoff has no complete property response');
}

OwnerAddPropertyFormState _readyForm() {
  final seed = OwnerAddPropertyMapper.fromProperty(
    PropertyDetailsModel.fromJson(_handoffProperty()),
  ).form;
  return seed.copyWith(
    photoDrafts: [
      ...seed.photoDrafts,
      for (var index = seed.photoCount; index < 10; index++)
        OwnerPropertyPhotoDraft(file: File('/tmp/property-$index.jpg')),
    ],
  );
}

class _HandoffRepository implements BaseRepository {
  final List<CrudBaseParmas> requests = [];
  String message = '';
  Map<String, dynamic> response = {};
  Completer<Map<String, dynamic>>? pending;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests.add(params);
    final json = pending == null ? response : await pending!.future;
    return Success(
      BaseModel<T>(key: '', msg: message, data: params.mapper!(json)),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _PropertyUploadAdapter implements HttpClientAdapter {
  _PropertyUploadAdapter(this.response);

  final Map<String, dynamic> response;
  RequestOptions? request;
  String body = '';

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    request = options;
    body = utf8.decode(await requestStream!.expand((chunk) => chunk).toList());
    return ResponseBody.fromString(
      jsonEncode({'data': response}),
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
