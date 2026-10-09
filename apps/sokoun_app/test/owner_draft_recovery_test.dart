import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/owner/home/data/owner_draft_data.dart';
import 'package:sokoun_app/features/owner/home/data/owner_draft_reconcile_data.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_property_draft.dart';
import 'package:sokoun_app/features/owner/home/data/models/property_location.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/owner_draft_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => AccountSession.begin('alice'));
  test(
    'acknowledged form can resume uploads when only its revision advances',
    () {
      final saved = const PropertyDetailsModel.initial().copyWith(
        id: 'same-created-property',
        title: 'Submitted title',
        updatedAt: '2026-10-08T10:00:00Z',
        mainImageId: 'confirmed-cover',
      );
      expect(
        OwnerDraftReconcileData.matchesAcknowledged(
          saved,
          saved.copyWith(updatedAt: '2026-10-08T10:01:00Z'),
        ),
        isTrue,
      );
      expect(
        OwnerDraftReconcileData.matchesAcknowledged(
          saved,
          saved.copyWith(title: 'Changed on another device'),
        ),
        isFalse,
      );
      expect(
        OwnerDraftReconcileData.matchesAcknowledged(
          saved,
          saved.copyWith(mainImageId: 'another-cover'),
        ),
        isFalse,
      );
    },
  );
  test('a missing account cannot report a successful device save', () async {
    final store = OwnerDraftData(
      accountId: '',
      propertyId: '',
      supportDirectory: () async => throw StateError('Must not touch storage'),
    );
    await expectLater(
      store.write(
        OwnerPropertyDraft(form: OwnerAddPropertyFormState.initial()),
      ),
      throwsStateError,
    );
  });
  test(
    'a save after the owning session ended cannot report persistence',
    () async {
      AccountSession.begin('owner');
      final store = _MemoryOwnerDraftStore();
      final cubit = OwnerDraftCubit(store: store);
      AccountSession.end();
      await expectLater(
        cubit.save(
          OwnerPropertyDraft(form: OwnerAddPropertyFormState.initial()),
        ),
        throwsStateError,
      );
      expect(store.state.form, isNull);
      await cubit.close();
    },
  );
  test(
    'storage errors are visible and a successful retry clears the warning',
    () async {
      final store = _MemoryOwnerDraftStore()..fail = true;
      final cubit = OwnerDraftCubit(store: store);
      final draft = OwnerPropertyDraft(
        form: OwnerAddPropertyFormState.initial().copyWith(
          title: 'Keep my form',
        ),
      );
      await expectLater(cubit.save(draft), throwsStateError);
      expect(cubit.state.localSaveFailed, isTrue);
      store.fail = false;
      await cubit.save(draft);
      expect(cubit.state.localSaveFailed, isFalse);
      expect(cubit.state.form?.title, 'Keep my form');
      await cubit.close();
    },
  );

  test(
    'closing still releases the cubit when a pending draft cannot be saved',
    () async {
      final store = _MemoryOwnerDraftStore()..fail = true;
      final cubit = OwnerDraftCubit(store: store);
      cubit.schedule(
        OwnerPropertyDraft(form: OwnerAddPropertyFormState.initial()),
      );
      await expectLater(cubit.close(), throwsStateError);
      expect(cubit.isClosed, isTrue);
    },
  );
  test(
    'restart restores media and uploaded IDs after the picker files disappear',
    () async {
      final root = await Directory.systemTemp.createTemp('sokoun-draft-test');
      addTearDown(() => root.delete(recursive: true));
      final picker = await Directory('${root.path}/picker').create();
      final photo = await File(
        '${picker.path}/photo.jpg',
      ).writeAsBytes([1, 2, 3]);
      final video = await File('${picker.path}/video.mp4').writeAsBytes([4, 5]);
      final proof = await File('${picker.path}/proof.jpg').writeAsBytes([6, 7]);
      final form = OwnerAddPropertyFormState.initial().copyWith(
        title: 'Near work',
        governorateId: 'gov',
        governorate: 'Cairo',
        districtId: 'city',
        district: 'Maadi',
        street: 'Street',
        location: const PropertyLocation(latitude: 30, longitude: 31),
        photoDrafts: [
          const OwnerPropertyPhotoDraft(
            existingId: 'uploaded-cover',
            existingUrl: 'https://example.invalid/cover.jpg',
            name: 'Living room',
          ),
          OwnerPropertyPhotoDraft(
            file: photo,
            name: 'Bedroom',
            description: 'Bright room',
          ),
        ],
        videoFile: video,
        videoDuration: 30,
        ownershipProofFile: proof,
        deposit: 'one_month',
        rentalUnit: 'monthly',
        monthlyPrice: '18000',
        rentalDuration: '6',
        amenities: {'wifi'},
        smokingAllowed: false,
        optionLabels: {'wifi': 'WiFi'},
      );
      OwnerDraftData store(String account) => OwnerDraftData(
        accountId: account,
        propertyId: '',
        supportDirectory: () async => root,
      );
      final saved = await store('alice').write(
        OwnerPropertyDraft(
          form: form,
          step: 2,
          savedProperty: const PropertyDetailsModel.initial().copyWith(
            id: 'created-property',
          ),
          isServerSnapshotCurrent: true,
        ),
      );
      await picker.delete(recursive: true);
      final recovered = await store('alice').read();
      expect(recovered.step, 2);
      expect(recovered.savedProperty?.id, 'created-property');
      expect(recovered.isServerSnapshotCurrent, isFalse);
      expect(recovered.form?.photoDrafts.first.existingId, 'uploaded-cover');
      expect(recovered.form?.photoDrafts.last.description, 'Bright room');
      expect(await recovered.form!.photoDrafts.last.file!.readAsBytes(), [
        1,
        2,
        3,
      ]);
      expect(await recovered.form!.videoFile!.readAsBytes(), [4, 5]);
      expect(recovered.form!.ownershipProofFile, isNull);
      expect(recovered.needsPrivateDocument, isTrue);
      expect(
        OwnerDraftFormCodec.encode(recovered.form!),
        OwnerDraftFormCodec.encode(saved.form!),
      );
      expect((await store('bob').read()).form, isNull);
      await store('alice').clear();
      expect((await store('alice').read()).form, isNull);
    },
  );

  test(
    'missing files invalidate the saved snapshot instead of passing upload validation',
    () async {
      final root = await Directory.systemTemp.createTemp(
        'sokoun-draft-missing',
      );
      addTearDown(() => root.delete(recursive: true));
      final original = await File(
        '${root.path}/original.jpg',
      ).writeAsBytes([1]);
      final store = OwnerDraftData(
        accountId: 'alice',
        propertyId: 'property',
        supportDirectory: () async => root,
      );
      final saved = await store.write(
        OwnerPropertyDraft(
          form: OwnerAddPropertyFormState.initial().copyWith(
            photoDrafts: [OwnerPropertyPhotoDraft(file: original)],
          ),
          isServerSnapshotCurrent: true,
        ),
      );
      await saved.form!.photoDrafts.single.file!.delete();
      final recovered = await store.read();
      expect(recovered.hasMissingFiles, isTrue);
      expect(recovered.isServerSnapshotCurrent, isFalse);
      expect(recovered.form!.photoDrafts.single.needsReselection, isTrue);
      expect(recovered.form!.photoDrafts.single.file, isNotNull);
    },
  );

  test(
    'flushing a debounced edit saves the latest form before closing',
    () async {
      final root = await Directory.systemTemp.createTemp('sokoun-draft-flush');
      addTearDown(() => root.delete(recursive: true));
      final store = OwnerDraftData(
        accountId: 'alice',
        propertyId: '',
        supportDirectory: () async => root,
      );
      final cubit = OwnerDraftCubit(store: store);
      await cubit.load();
      cubit.schedule(
        OwnerPropertyDraft(
          form: OwnerAddPropertyFormState.initial().copyWith(title: 'First'),
        ),
      );
      cubit.schedule(
        OwnerPropertyDraft(
          form: OwnerAddPropertyFormState.initial().copyWith(title: 'Final'),
        ),
      );
      await cubit.close();
      expect((await store.read()).form?.title, 'Final');
    },
  );
}

class _MemoryOwnerDraftStore implements OwnerDraftStore {
  bool fail = false;
  OwnerPropertyDraft state = const OwnerPropertyDraft.initial();
  @override
  Future<OwnerPropertyDraft> read() async => state;
  @override
  Future<OwnerPropertyDraft> write(OwnerPropertyDraft draft) async {
    if (fail) throw StateError('Device storage is unavailable');
    state = draft;
    return draft;
  }

  @override
  Future<void> clear() async {
    state = const OwnerPropertyDraft.initial();
  }
}
