import 'dart:io';

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
    return nationalId.trim().length == 14 &&
        (frontIdImage != null || frontIdFileName != null) &&
        (backIdImage != null || backIdFileName != null) &&
        (selfieImage != null || selfieFileName != null);
  }

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
