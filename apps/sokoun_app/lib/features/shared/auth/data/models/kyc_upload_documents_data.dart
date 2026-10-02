import 'dart:io';
import 'package:melos_core/core/helpers/account_input_rules.dart';

import 'register.dart';

class KycUploadDocumentsData {
  final String nationalId;
  final File? frontIdImage;
  final File? backIdImage;
  final File? selfieImage;
  final String? frontIdFileName;
  final String? backIdFileName;
  final String? selfieFileName;

  const KycUploadDocumentsData({
    this.nationalId = '',
    this.frontIdImage,
    this.backIdImage,
    this.selfieImage,
    this.frontIdFileName,
    this.backIdFileName,
    this.selfieFileName,
  });

  bool get canSubmit {
    return AccountInputRules.isValidEgyptianNationalId(nationalId) &&
        frontIdImage != null &&
        backIdImage != null &&
        selfieImage != null;
  }

  bool get hasChanges =>
      nationalId.trim().isNotEmpty ||
      frontIdImage != null ||
      backIdImage != null ||
      selfieImage != null;

  /// Existing documents may be omitted; the server identifies missing fields.
  Map<String, dynamic> toJson() => {
    if (nationalId.trim().isNotEmpty) 'national_id': nationalId.trim(),
    if (frontIdImage != null) 'front_id_image': frontIdImage,
    if (backIdImage != null) 'back_id_image': backIdImage,
    if (selfieImage != null) 'selfie_image': selfieImage,
  };

  KycDocumentUploadData toUploadData() => KycDocumentUploadData(
    nationalId: nationalId.trim(),
    frontIdImage: frontIdImage,
    backIdImage: backIdImage,
    selfieImage: selfieImage,
  );

  KycUploadDocumentsData copyWith({
    String? nationalId,
    File? frontIdImage,
    File? backIdImage,
    File? selfieImage,
    String? frontIdFileName,
    String? backIdFileName,
    String? selfieFileName,
  }) => KycUploadDocumentsData(
    nationalId: nationalId ?? this.nationalId,
    frontIdImage: frontIdImage ?? this.frontIdImage,
    backIdImage: backIdImage ?? this.backIdImage,
    selfieImage: selfieImage ?? this.selfieImage,
    frontIdFileName: frontIdFileName ?? this.frontIdFileName,
    backIdFileName: backIdFileName ?? this.backIdFileName,
    selfieFileName: selfieFileName ?? this.selfieFileName,
  );
}
