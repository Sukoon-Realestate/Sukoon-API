import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:path_provider/path_provider.dart';
import '../../../shared/recovery/data/private_recovery_data.dart';
import '../../../shared/recovery/data/recovery_scope.dart';
import 'models/owner_add_property_content.dart';
import 'models/owner_property_draft.dart';

abstract interface class OwnerDraftStore {
  Future<OwnerPropertyDraft> read();
  Future<OwnerPropertyDraft> write(OwnerPropertyDraft draft);
  Future<void> clear();
}

class OwnerDraftData implements OwnerDraftStore {
  OwnerDraftData({
    required this.accountId,
    required this.propertyId,
    Future<Directory> Function()? supportDirectory,
    RecoveryStorage storage = const ProtectedRecoveryStorage(),
    String? environment,
  }) : _supportDirectory = supportDirectory ?? getApplicationSupportDirectory,
       _environment = environment {
    _store = PrivateDraftStore(
      scope: _resolveScope,
      encode: (value) => value.toJson(),
      decode: OwnerPropertyDraft.fromJson,
      storage: storage,
    );
  }
  static const int mediaBudgetBytes = 256 * 1024 * 1024;
  static Future<void>? _mediaWork;
  static bool _cleanupRegistered = false;
  final String accountId;
  final String propertyId;
  final Future<Directory> Function() _supportDirectory;
  final String? _environment;
  Future<RecoveryScope>? _scope;
  Future<RecoveryScope> _resolveScope() => _scope ??= () async {
    final String environment =
        _environment ?? await RecoveryScope.currentEnvironment();
    return RecoveryScope(
      environment: environment,
      accountId: accountId,
      flow: 'property',
      entityId: propertyId.isEmpty ? 'new' : propertyId,
      workspace: 'owner',
    );
  }();
  late final PrivateDraftStore<OwnerPropertyDraft> _store;
  final int _generation = AccountSession.generation;
  final Map<String, String> _copiedPaths = {};
  static String _component(String value) =>
      base64Url.encode(utf8.encode(value));
  static void initialize() {
    PrivateRecoveryData.initialize();
    if (_cleanupRegistered) return;
    _cleanupRegistered = true;
    AccountSession.registerCleanup((account) async {
      await _mediaWork;
      final Directory root = await getApplicationSupportDirectory();
      final Directory media = Directory('${root.path}/sokoun_listing_media_v2');
      if (await media.exists()) {
        await for (final FileSystemEntity environment in media.list()) {
          if (environment is! Directory) continue;
          final Directory owned = Directory(
            '${environment.path}/${_component(account)}',
          );
          if (await owned.exists()) await owned.delete(recursive: true);
        }
      }
      final Directory legacy = Directory(
        '${root.path}/sokoun_listing_drafts/${_component(account)}',
      );
      if (await legacy.exists()) await legacy.delete(recursive: true);
    });
  }

  Future<Directory> _directory() async {
    final Directory root = await _supportDirectory();
    final RecoveryScope scope = await _resolveScope();
    return Directory(
      '${root.path}/sokoun_listing_media_v2/${_component(scope.environment)}/${_component(accountId)}/${_component(propertyId.isEmpty ? 'new' : propertyId)}',
    );
  }

  Future<void> _purgeLegacy() async {
    final Directory root = await _supportDirectory();
    final Directory legacy = Directory(
      '${root.path}/sokoun_listing_drafts/${_component(accountId)}/${_component(propertyId.isEmpty ? 'new' : propertyId)}',
    );
    final File manifest = File('${legacy.path}/draft.json');
    if (!await manifest.exists()) return;
    try {
      final Map json = jsonDecode(await manifest.readAsString()) as Map;
      final Object? proof = (json['form'] as Map?)?['proof_path'];
      if (proof is String &&
          File(proof).absolute.path.startsWith(
            '${legacy.absolute.path}${Platform.pathSeparator}',
          )) {
        final File copy = File(proof);
        if (await copy.exists()) await copy.delete();
      }
    } catch (_) {
      /* Never follow paths from corrupt metadata. */
    }
    await manifest.delete();
  }

  @override
  Future<OwnerPropertyDraft> read() async {
    initialize();
    if (accountId.isEmpty || accountId == '0') {
      return const OwnerPropertyDraft.initial();
    }
    await _purgeLegacy();
    final OwnerPropertyDraft? draft = (await _store.read())?.value;
    if (draft?.form == null) return const OwnerPropertyDraft.initial();
    final OwnerAddPropertyFormState form = draft!.form!;
    final List<OwnerPropertyPhotoDraft> photos = [];
    bool missing = draft.needsPrivateDocument;
    for (final OwnerPropertyPhotoDraft photo in form.photoDrafts) {
      final bool absent =
          !photo.isExisting &&
          (photo.file == null || !await photo.file!.exists());
      missing = missing || absent;
      photos.add(photo.copyWith(needsReselection: absent));
    }
    final bool missingVideo =
        form.videoFile != null && !await form.videoFile!.exists();
    return draft.copyWith(
      form: form.copyWith(photoDrafts: photos, clearVideo: missingVideo),
      hasMissingFiles: missing || missingVideo,
      isServerSnapshotCurrent: false,
    );
  }

  Future<int> _mediaBytes() async {
    final Directory root = await _supportDirectory();
    final Directory media = Directory('${root.path}/sokoun_listing_media_v2');
    int bytes = 0;
    if (await media.exists()) {
      await for (final FileSystemEntity entity in media.list(
        recursive: true,
        followLinks: false,
      )) {
        if (entity is File) bytes += await entity.length();
      }
    }
    return bytes;
  }

  Future<File?> _copy(File? source, Directory directory) async {
    if (source == null) return null;
    if (!await source.exists()) return source;
    if (source.absolute.path.startsWith(
      '${directory.absolute.path}${Platform.pathSeparator}',
    )) {
      return source;
    }
    final FileStat sourceStat = await source.stat();
    final String sourceVersion =
        '${source.path}|${sourceStat.size}|${sourceStat.modified.microsecondsSinceEpoch}';
    final String? previous = _copiedPaths[sourceVersion];
    if (previous != null && await File(previous).exists()) {
      return File(previous);
    }
    if (await _mediaBytes() + await source.length() > mediaBudgetBytes) {
      throw StateError(LocaleKeys.professionalMediaBudget);
    }
    final String name = source.path.split(Platform.pathSeparator).last;
    final File target = File(
      '${directory.path}/${DateTime.now().microsecondsSinceEpoch}_$name',
    );
    await source.copy(target.path);
    _copiedPaths[sourceVersion] = target.path;
    return target;
  }

  @override
  Future<OwnerPropertyDraft> write(OwnerPropertyDraft draft) {
    initialize();
    Future<OwnerPropertyDraft> save() async {
      if (_generation != AccountSession.generation ||
          accountId.isEmpty ||
          accountId == '0' ||
          draft.form == null) {
        throw StateError(LocaleKeys.freeLocalSaveFailed);
      }
      final Directory directory = await _directory();
      await directory.create(recursive: true);
      final OwnerAddPropertyFormState form = draft.form!;
      final List<OwnerPropertyPhotoDraft> photos = [];
      for (final OwnerPropertyPhotoDraft photo in form.photoDrafts) {
        photos.add(
          photo.copyWith(
            file: await _copy(photo.file, directory),
            draftKey: photo.reference,
          ),
        );
      }
      final OwnerPropertyDraft saved = draft.copyWith(
        form: form.copyWith(
          photoDrafts: photos,
          videoFile: await _copy(form.videoFile, directory),
          clearOwnershipProof: true,
        ),
        needsPrivateDocument:
            form.ownershipProofFile != null || draft.needsPrivateDocument,
        savedAt: DateTime.now(),
      );
      await _store.write(saved, serverRevision: saved.baseRevision);
      final Set<String?> retained = {
        for (final photo in photos) photo.file?.path,
        saved.form?.videoFile?.path,
      };
      await for (final FileSystemEntity entity in directory.list(
        followLinks: false,
      )) {
        if (entity is File && !retained.contains(entity.path)) {
          await entity.delete();
        }
      }
      return saved;
    }

    final Future<OwnerPropertyDraft> work = _mediaWork == null
        ? Future.sync(save)
        : _mediaWork!.then((_) => save());
    late final Future<void> tail;
    void release() {
      if (identical(_mediaWork, tail)) _mediaWork = null;
    }

    tail = work.then<void>(
      (_) => release(),
      onError: (Object _, StackTrace __) => release(),
    );
    _mediaWork = tail;
    return work;
  }

  @override
  Future<void> clear() async {
    await _mediaWork;
    await _store.clear();
    final Directory directory = await _directory();
    if (await directory.exists()) await directory.delete(recursive: true);
    _copiedPaths.clear();
  }
}
