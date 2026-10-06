import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/owner/properties/presentation/cubits/delete_owner_property_cubit.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:toastification/toastification.dart';

void main() {
  late _FeedbackRepository repository;

  setUp(() async {
    await injector.reset();
    toastification.managers.clear();
    repository = _FeedbackRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
  });

  tearDown(() async {
    toastification.dismissAll(delayForAnimation: false);
    await injector.reset();
  });

  Future<void> mount(WidgetTester tester) async {
    await tester.pumpWidget(
      ScreenUtilInit(
        designSize: const Size(390, 844),
        builder: (_, _) =>
            MaterialApp(navigatorKey: Go.navigatorKey, home: const Scaffold()),
      ),
    );
    await tester.pumpAndSettle();
  }

  final Map<String, Future<void> Function()> operations = {
    'password change': () async {
      final cubit = ChangePasswordCubit();
      addTearDown(cubit.close);
      await cubit.save(const ChangePasswordBody.initial());
    },
    'profile edit': () async {
      final cubit = ProfileEditCubit();
      addTearDown(cubit.close);
      await cubit.editProfile(
        body: const ProfileEditBody.initial(),
        onSuccess: () {},
      );
    },
    'visit cancellation': () async {
      final cubit = VisitCancelCubit();
      addTearDown(cubit.close);
      await cubit.cancel('visit-id');
    },
    'visit review': () async {
      final cubit = VisitReviewCubit();
      addTearDown(cubit.close);
      await cubit.submit(
        visitId: 'visit-id',
        body: const VisitReviewBody(
          cleanliness: 5,
          accuracy: 4,
          ownerInteraction: 3,
          comment: '',
        ),
      );
    },
    'accept visit': () async {
      final cubit = OwnerVisitStatusCubit();
      addTearDown(cubit.close);
      await cubit.acceptVisitRequest(requestId: 'visit-id', onSuccess: () {});
    },
    'reject visit': () async {
      final cubit = OwnerVisitStatusCubit();
      addTearDown(cubit.close);
      await cubit.rejectVisitRequest(requestId: 'visit-id', onSuccess: () {});
    },
    'property deletion': () async {
      final cubit = DeleteOwnerPropertyCubit();
      addTearDown(cubit.close);
      await cubit.delete(propertyId: 'property-id', onSuccess: () {});
    },
  };

  for (final operation in operations.entries) {
    testWidgets('${operation.key} displays the current API success message', (
      tester,
    ) async {
      await mount(tester);
      repository.message = 'Server confirmation for ${operation.key}';
      await operation.value();
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 250));
      expect(find.text(repository.message), findsOneWidget);
      expect(find.byType(SnackBar), findsNothing);

      toastification.dismissAll(delayForAnimation: false);
      await tester.pump(const Duration(seconds: 1));
      repository.message = 'Updated server wording for ${operation.key}';
      await operation.value();
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 250));
      expect(find.text(repository.message), findsOneWidget);
      toastification.dismissAll(delayForAnimation: false);
      await tester.pump(const Duration(seconds: 1));
    });

    testWidgets('${operation.key} does not invent a missing API message', (
      tester,
    ) async {
      await mount(tester);
      repository.message = '';
      await operation.value();
      await tester.pump();
      expect(
        toastification.managers.values.expand(
          (manager) => manager.notifications,
        ),
        isEmpty,
      );
    });
  }

  testWidgets('API failure text reaches the error toast unchanged', (
    tester,
  ) async {
    await mount(tester);
    repository.failure = 'Server validation: password has expired';
    await operations['password change']!();
    await tester.pump();
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));
    expect(find.text(repository.failure!), findsOneWidget);
    toastification.dismissAll(delayForAnimation: false);
    await tester.pump(const Duration(seconds: 1));
  });

  testWidgets('an unconfirmed deletion preserves the API message', (
    tester,
  ) async {
    await mount(tester);
    repository.payload = {'id': 'property-id', 'deleted': false};
    repository.message = 'This property could not be deleted';
    final cubit = DeleteOwnerPropertyCubit();
    addTearDown(cubit.close);
    await cubit.delete(
      propertyId: 'property-id',
      onSuccess: () => fail('Unconfirmed deletion was accepted'),
    );
    expect(cubit.state.isError, isTrue);
    expect(cubit.state.msg, repository.message);
    expect(
      toastification.managers.values.expand((manager) => manager.notifications),
      isEmpty,
    );
  });

  testWidgets('the shared toast keeps Undo and dismisses before restoring', (
    tester,
  ) async {
    await mount(tester);
    int restored = 0;
    Messages.showToast(
      msg: 'Removed by the server',
      actionLabel: 'Undo',
      onAction: () => restored++,
    );
    await tester.pump();
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));
    expect(find.text('Removed by the server'), findsOneWidget);
    await tester.tap(find.text('Undo'));
    await tester.tap(find.text('Undo'));
    await tester.pump(const Duration(seconds: 1));
    expect(restored, 1);
    expect(find.text('Undo'), findsNothing);
  });
}

class _FeedbackRepository implements BaseRepository {
  String message = '';
  String? failure;
  Map<String, dynamic> payload = {'id': 'property-id', 'deleted': true};

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    if (failure case final message?) return Error(ServerFailure(message));
    return Success(
      BaseModel<T>(key: 'success', msg: message, data: params.mapper!(payload)),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}
