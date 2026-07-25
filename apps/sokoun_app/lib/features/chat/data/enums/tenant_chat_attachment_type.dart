enum TenantChatAttachmentType { camera, photos, file, location }

extension TenantChatAttachmentTypeX on TenantChatAttachmentType {
  bool get isCamera => this == TenantChatAttachmentType.camera;
  bool get isPhotos => this == TenantChatAttachmentType.photos;
  bool get isFile => this == TenantChatAttachmentType.file;
  bool get isLocation => this == TenantChatAttachmentType.location;
}
