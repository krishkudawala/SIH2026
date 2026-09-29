import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/utils/responsive.dart';

// --- Theme Colors Placeholder ---
const Color surfaceWhite = Colors.white;
const Color institutionalBlue = Colors.blue;
const Color textSecondary = Colors.black54;
const Color badgeRed = Colors.red;

// --- Data Class ---
class BottomNavItem {
  final String label;
  final IconData icon;
  final String route;
  final int badgeCount; // 0 = no badge

  const BottomNavItem({
    required this.label,
    required this.icon,
    required this.route,
    this.badgeCount = 0,
  });
}

// 5 items, matching the screenshot: Home, Lots, Scan (center), Review (badge), More
const List<BottomNavItem> bottomNavItems = [
  BottomNavItem(label: "Home", icon: Icons.home_outlined, route: "/home"),
  BottomNavItem(label: "Lots", icon: Icons.list_alt_outlined, route: "/lots"),
  BottomNavItem(label: "Scan", icon: Icons.camera_alt_outlined, route: "/scan"),
  BottomNavItem(
    label: "Review",
    icon: Icons.rate_review_outlined,
    route: "/review",
    badgeCount: 1,
  ),
  BottomNavItem(label: "More", icon: Icons.more_horiz, route: "/more"),
];

// --- Component ---
class MandiBottomNavBar extends StatelessWidget {
  final String currentRoute;
  final ValueChanged<String> onNavigate;

  const MandiBottomNavBar({
    super.key,
    required this.currentRoute,
    required this.onNavigate,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 74.0,
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.topCenter,
        children: [
          // Bar background
          Positioned.fill(
            top: 12,
            child: Container(
              decoration: BoxDecoration(
                color: surfaceWhite,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 8,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: Row(
                children: bottomNavItems.map((item) {
                  final bool isScan = item.route == "/scan";
                  return Expanded(
                    child: isScan
                    // Leave empty space under the raised scan button
                        ? const SizedBox.shrink()
                        : _NavItem(
                      item: item,
                      selected: currentRoute == item.route,
                      onTap: () => onNavigate(item.route),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          // Raised circular Scan button
          Positioned(
            top: 0,
            child: _ScanButton(
              selected: currentRoute == "/scan",
              onTap: () => onNavigate("/scan"),
            ),
          ),
        ],
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final BottomNavItem item;
  final bool selected;
  final VoidCallback onTap;

  const _NavItem({
    required this.item,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color = selected ? institutionalBlue : textSecondary;

    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                Icon(item.icon, color: color, size: 22.0),
                if (item.badgeCount > 0)
                  Positioned(
                    right: -6,
                    top: -4,
                    child: Container(
                      padding: const EdgeInsets.all(3),
                      constraints:
                      const BoxConstraints(minWidth: 16, minHeight: 16),
                      decoration: const BoxDecoration(
                        color: badgeRed,
                        shape: BoxShape.circle,
                      ),
                      child: Text(
                        '${item.badgeCount}',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          height: 1.2,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              item.label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: color,
                fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ScanButton extends StatelessWidget {
  final bool selected;
  final VoidCallback onTap;

  const _ScanButton({required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 52,
        height: 52,
        decoration: BoxDecoration(
          color: institutionalBlue,
          shape: BoxShape.circle,
          border: Border.all(color: surfaceWhite, width: 3),
          boxShadow: [
            BoxShadow(
              color: institutionalBlue.withOpacity(0.35),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: const Icon(
          Icons.camera_alt,
          color: Colors.white,
          size: 24.0,
        ),
      ),
    );
  }
}