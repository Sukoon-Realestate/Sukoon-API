import 'package:melos_core/core/helpers/cache_service.dart';
import 'helpers/account_test_dependencies.dart';
import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/auth/data/models/register.dart';
import 'package:sokoun_app/features/shared/auth/data/models/otp.dart';
import 'package:sokoun_app/features/shared/auth/data/models/google_login.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/models/property_location.dart';
import 'package:sokoun_app/features/owner/home/data/models/upload_property_image_body.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/property_submission_cubit.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final requests = _requests();
  Map<String, dynamic> contract(String method, String path) => requests
      .firstWhere((r) => r['method'] == method && _path(r).endsWith(path));
  void matches(
    Map<String, dynamic> body,
    String method,
    String path, {
    bool partial = false,
  }) {
    final expected = _body(contract(method, path));
    if (method == 'POST' && path == '/properties/create/') {
      // The sample multipart request omits these optional amenities. They are
      // documented by the creation response and the confirmed filter lookup.
      expected.addAll({
        'has_electricity_meter': false,
        'has_water_meter': false,
      });
      // Proposed property extensions are defined in
      // docs/property_media_edit_delete_backend.md; collection.json still
      // records the existing server contract until the backend is deployed.
      expected.addAll({
        'street': '',
        'country': '',
        'building_year': '',
        'deposit': '',
        'smoking_allowed': '',
        'main_image_name': '',
        'main_image_description': '',
        'amenities': '[]',
        'video': '',
        'video_duration': 0,
      });
    }
    expect(
      body.keys.toSet().difference(expected.keys.toSet()),
      isEmpty,
      reason: '$method $path must not send undocumented fields',
    );
    if (!partial) expect(body.keys.toSet(), expected.keys.toSet());
  }

  setUpAll(CacheStorage.init);

  setUp(() async {
    await injector.reset();
    await registerAuthenticatedTestAccount();
  });
  tearDown(() => injector.reset());

  test(
    'registration matches the JSON collection even if legacy docs are present',
    () {
      final body = RegisterBody(
        firstName: 'A',
        lastName: 'B',
        phone: '01012345678',
        email: 'a@example.com',
        password: 'password',
        rePassword: 'password',
        nationalId: '123',
        frontIdImage: File('/tmp/front.jpg'),
      );
      matches(body.toJson(), 'POST', '/auth/users/');
      expect(body.toJson()['phone_number'], '01012345678');
      expect(RegisterBody.fromJson(body.toJson()).phone, body.phone);
    },
  );
  test('OTP and Google sign in match their request bodies', () {
    matches(
      const VerifyOtpBody(email: 'a@example.com', otp: '123456').toJson(),
      'POST',
      '/auth/verify/',
    );
    matches(
      const ResendOtpBody(email: 'a@example.com').toJson(),
      'POST',
      '/auth/resend-otp/',
    );
    matches(
      const GoogleLoginBody(token: 'id-token').toJson(),
      'POST',
      '/auth/google/',
    );
  });
  test('profile bodies target their documented fields', () {
    final body = ProfileEditBody(
      avatar: File('/tmp/avatar.jpg'),
      fullName: 'First Last',
      gender: 'male',
      phoneNumber: '01012345678',
    );
    matches(body.toJson(), 'PATCH', '/profiles/edit/');
    matches(
      body.toUserJson(),
      'PATCH',
      '/profiles/user/update/',
      partial: true,
    );
    expect(body.toUserJson().containsKey('avatar'), isFalse);
  });
  test(
    'booking uses seconds and review omits server calculated overall rating',
    () {
      final body = BookVisitBody.fromTime(
        visitDate: '2026-10-12',
        hour: 14,
        minute: 30,
        note: 'Visit',
      );
      matches(body.toJson(), 'POST', '/visits/');
      expect(body.toJson()['visit_time'], '14:30:00');
      expect(
        const BookVisitBody(
          visitDate: '',
          visitTime: '09:00',
          note: '',
        ).toJson()['visit_time'],
        '09:00:00',
      );
      matches(
        const VisitReviewBody(
          cleanliness: 4,
          accuracy: 5,
          ownerInteraction: 4,
          comment: 'Good',
        ).toJson(),
        'POST',
        '/review/',
      );
    },
  );
  test(
    'property body keeps the existing contract and adds the proposed property fields',
    () {
      final form = _property();
      final body = form.toJson();
      matches(body, 'POST', '/properties/create/', partial: true);
      expect(body['latitude'], '30.044400');
      expect(body['longitude'], '31.235700');
      expect(body['district'], 'Maadi');
      expect(body['city'], 'city-id');
      expect(body['suitable_for'], 'singles');
      expect(body['main_image'], isA<File>());
      expect(body['has_electricity_meter'], isFalse);
      expect(body['has_water_meter'], isFalse);
      expect(
        form.toJson(includeMainImage: false).containsKey('main_image'),
        isFalse,
      );
      // Gallery files use the dedicated endpoint so per-photo metadata is retained.
      final photo = UploadPropertyImageBody(
        image: File('/tmp/photo.jpg'),
        name: 'Room',
        description: 'Main room',
      );
      matches(photo.toJson(), 'POST', '/images/');
    },
  );
  test(
    'property create rejects unselected or invalid coordinates before the network',
    () async {
      final repository = _Repository();
      injector.registerSingleton<BaseCrudUseCase>(
        BaseCrudUseCase(repository: repository),
      );
      final cubit = PropertySubmissionCubit();
      addTearDown(cubit.close);
      final form = _property().copyWith(
        videoFile: File('/tmp/tour.mp4'),
        videoDuration: 45,
      );
      await cubit.save(
        form: form.copyWith(clearLocation: true),
        onSuccess: (_) {},
      );
      await cubit.save(
        form: form.copyWith(
          location: const PropertyLocation(latitude: 100, longitude: 200),
        ),
        onSuccess: (_) {},
      );
      expect(repository.calls, isEmpty);
      await cubit.save(form: form, onSuccess: (_) {});
      expect(repository.calls.single.isFromData, isTrue);
      matches(
        repository.calls.single.body!,
        'POST',
        '/properties/create/',
        partial: true,
      );
    },
  );
  test(
    'availability saves with collection verb and nested slot body',
    () async {
      final repository = _Repository();
      injector.registerSingleton<BaseCrudUseCase>(
        BaseCrudUseCase(repository: repository),
      );
      final cubit = OwnerAvailabilityCubit();
      addTearDown(cubit.close);
      const body = OwnerAvailabilitySaveBody(
        availabilityDate: '2026-10-12',
        slots: [
          OwnerAvailabilitySlotBody(time: '09:00:00', isEnabled: true),
          OwnerAvailabilitySlotBody(time: '12:00:00', isEnabled: false),
        ],
      );
      expect(
        await cubit.saveAvailability(ownerPropertyId: 'p', body: body),
        isTrue,
      );
      matches(repository.calls.single.body!, 'PUT', '/availability/');
      expect(repository.calls.single.httpRequestType, HttpRequestType.put);
      final expectedSlot =
          (_body(contract('PUT', '/availability/'))['slots'] as List).first
              as Map;
      expect(
        body.toJson()['slots'].first.keys.toSet(),
        expectedSlot.keys.toSet(),
      );
    },
  );
}

OwnerAddPropertyFormState _property() =>
    OwnerAddPropertyFormState.initial().copyWith(
      title: 'Studio',
      propertyType: 'studio',
      governorateId: 'governorate-id',
      governorate: 'Cairo',
      districtId: 'city-id',
      district: 'Cairo',
      street: 'Maadi',
      bedrooms: '1',
      bathrooms: '1',
      space: '55',
      floor: '0',
      location: const PropertyLocation(latitude: 30.0444, longitude: 31.2357),
      monthlyPrice: '7000',
      rentalDuration: '3',
      rentalUnit: 'monthly',
      suitableFor: 'individuals',
      description: 'Studio near the metro',
      photoDrafts: List.generate(
        10,
        (index) => OwnerPropertyPhotoDraft(file: File('/tmp/photo-$index.jpg')),
      ),
    );

List<Map<String, dynamic>> _requests() {
  final json =
      jsonDecode(File('../../collection.json').readAsStringSync()) as Map;
  final result = <Map<String, dynamic>>[];
  void walk(List items) {
    for (final item in items) {
      if (item['item'] is List) walk(item['item']);
      if (item['request'] is Map) {
        result.add(Map<String, dynamic>.from(item['request']));
      }
    }
  }

  walk(json['collection']['item']);
  return result;
}

String _path(Map<String, dynamic> request) =>
    (request['url'] is Map ? request['url']['raw'] : request['url']) as String;
Map<String, dynamic> _body(Map<String, dynamic> request) {
  final body = request['body'] as Map;
  if (body['mode'] == 'formdata') {
    return {
      for (final field in body['formdata'])
        if (field['disabled'] != true) field['key'] as String: field['type'],
    };
  }
  return jsonDecode((body['raw'] as String).replaceAll(RegExp(r'//[^\n]*'), ''))
      as Map<String, dynamic>;
}

class _Repository implements BaseRepository {
  final List<CrudBaseParmas> calls = [];
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    calls.add(params);
    return Success(
      BaseModel<T>(key: '', msg: '', data: params.mapper!({'id': 'p'})),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}
