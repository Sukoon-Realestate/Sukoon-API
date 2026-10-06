class HomeNavigationDestination {
  const HomeNavigationDestination({
    required this.icon,
    required this.selectedIcon,
    required this.label,
    this.badgeCount = 0,
  });

  final Object icon;
  final Object selectedIcon;
  final String label;
  final int badgeCount;
}
