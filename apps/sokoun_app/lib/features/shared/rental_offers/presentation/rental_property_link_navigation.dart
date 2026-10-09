import '../../destinations/data/destination_resolver.dart';
import '../../destinations/presentation/destination_navigation.dart';

abstract final class RentalPropertyLinkNavigation {
  static bool receive(Uri uri) {
    final target = DestinationResolver.propertyLink(uri);
    if (target == null) return false;
    DestinationNavigation.open(target);
    return true;
  }

  static void ready() => DestinationNavigation.ready();
  static void reset() => DestinationNavigation.reset();
}
