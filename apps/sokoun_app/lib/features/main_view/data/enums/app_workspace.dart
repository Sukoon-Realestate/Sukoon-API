enum AppWorkspace { tenant, owner }

extension AppWorkspaceX on AppWorkspace {
  bool get isOwner => this == AppWorkspace.owner;
  bool get isTenant => this == AppWorkspace.tenant;

  static AppWorkspace fromName(Object? value) =>
      value == 'owner' ? AppWorkspace.owner : AppWorkspace.tenant;
}
