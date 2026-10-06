import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
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
  }) : _supportDirectory = supportDirectory ?? getApplicationSupportDirectory;
  final String accountId;
  final String propertyId;
  final Future<Directory> Function() _supportDirectory;
  final Map<String, String> _copiedPaths = {};
  Future<Directory> _directory() async {
    final root = await _supportDirectory();
    return Directory(
      '${root.path}/sokoun_listing_drafts/${base64Url.encode(utf8.encode(accountId))}/${base64Url.encode(utf8.encode(propertyId.isEmpty ? 'new' : propertyId))}',
    );
  }

  @override
  Future<OwnerPropertyDraft> read() async {
    if (accountId.isEmpty || accountId == '0') {
      return const OwnerPropertyDraft.initial();
    }
    final directory = await _directory();
    final file = File('${directory.path}/draft.json');
    if (!await file.exists()) return const OwnerPropertyDraft.initial();
    var draft = OwnerPropertyDraft.fromJson(
      Map<String, dynamic>.from(jsonDecode(await file.readAsString()) as Map),
    );
    final form = draft.form;
    if (form == null) return draft;
    final photos = <OwnerPropertyPhotoDraft>[];
    var missing = false;
    for (final photo in form.photoDrafts) {
      if (photo.isExisting ||
          photo.file != null && await photo.file!.exists()) {
        photos.add(photo);
      } else {
        missing = true;
      }
    }
    final missingVideo =
        form.videoFile != null && !await form.videoFile!.exists();
    final missingProof =
        form.ownershipProofFile != null &&
        !await form.ownershipProofFile!.exists();
    missing = missing || missingVideo || missingProof;
    draft = draft.copyWith(
      form: form.copyWith(
        photoDrafts: photos,
        clearVideo: missingVideo,
        clearOwnershipProof: missingProof,
      ),
      hasMissingFiles: missing,
      isServerSnapshotCurrent: missing ? false : draft.isServerSnapshotCurrent,
    );
    return draft;
  }

  Future<File?> _copy(File? source, Directory directory) async {
    if (source == null) return null;
    if (source.absolute.path.startsWith(
      '${directory.absolute.path}${Platform.pathSeparator}',
    )) {
      return source;
    }
    final previous = _copiedPaths[source.path];
    if (previous != null && await File(previous).exists()) {
      return File(previous);
    }
    final name = source.path.split(Platform.pathSeparator).last;
    final target = File(
      '${directory.path}/${DateTime.now().microsecondsSinceEpoch}_$name',
    );
    await source.copy(target.path);
    _copiedPaths[source.path] = target.path;
    return target;
  }

  @override
  Future<OwnerPropertyDraft> write(OwnerPropertyDraft draft) async {
    if (accountId.isEmpty || accountId == '0' || draft.form == null) {
      return draft;
    }
    final directory = await _directory();
    await directory.create(recursive: true);
    final form = draft.form!;
    final photos = <OwnerPropertyPhotoDraft>[];
    for (final photo in form.photoDrafts) {
      photos.add(photo.copyWith(file: await _copy(photo.file, directory)));
    }
    final saved = draft.copyWith(
      form: form.copyWith(
        photoDrafts: photos,
        videoFile: await _copy(form.videoFile, directory),
        ownershipProofFile: await _copy(form.ownershipProofFile, directory),
      ),
      savedAt: DateTime.now(),
    );
    // Rename only after the full manifest is flushed. A crash keeps the previous draft.
    final temporary = File('${directory.path}/draft.tmp');
    await temporary.writeAsString(jsonEncode(saved.toJson()), flush: true);
    await temporary.rename('${directory.path}/draft.json');
    final retained = {
      for (final photo in photos) photo.file?.path,
      saved.form?.videoFile?.path,
      saved.form?.ownershipProofFile?.path,
      '${directory.path}/draft.json',
    };
    await for (final entity in directory.list()) {
      if (entity is File && !retained.contains(entity.path)) {
        await entity.delete();
      }
    }
    return saved;
  }

  @override
  Future<void> clear() async {
    if (accountId.isEmpty || accountId == '0') return;
    final directory = await _directory();
    if (await directory.exists()) await directory.delete(recursive: true);
    _copiedPaths.clear();
  }
}
