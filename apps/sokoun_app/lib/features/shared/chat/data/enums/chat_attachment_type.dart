enum ChatAttachmentType { camera, photos, file, location }

extension ChatAttachmentTypeX on ChatAttachmentType {
  bool get isCamera => this == ChatAttachmentType.camera;
  bool get isPhotos => this == ChatAttachmentType.photos;
  bool get isFile => this == ChatAttachmentType.file;
  bool get isLocation => this == ChatAttachmentType.location;
}
