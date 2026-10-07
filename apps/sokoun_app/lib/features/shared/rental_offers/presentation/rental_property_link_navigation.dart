import 'package:flutter/widgets.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import '../data/models/rental_property_link.dart';

/// Retains startup links until account restoration and splash navigation finish.
abstract final class RentalPropertyLinkNavigation {
  static RentalPropertyLink? _pending;
  static bool _ready = false;
  static bool receive(Uri uri) {
    final link = RentalPropertyLink.parse(uri);
    if (link == null) return false;
    if (_ready) {
      _open(link);
    } else {
      _pending = link;
    }
    return true;
  }

  static void ready() {
    _ready = true;
    final link = _pending;
    _pending = null;
    if (link != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _open(link));
    }
  }

  static void reset() {
    _ready = false;
    _pending = null;
  }

  static void _open(RentalPropertyLink link) {
    void detail() => Go.to(
      PropertyDetailsScreen(propertyId: link.propertyId, offerId: link.offerId),
    );
    if (WorkspaceNavigation.isAuthenticated) {
      WorkspaceNavigation.open(workspace: AppWorkspace.tenant, detail: detail);
    } else {
      detail();
    }
  }
}
