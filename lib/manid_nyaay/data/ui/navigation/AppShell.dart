import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/bottom_nav_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';

/// Hosts the persistent bottom nav bar around the active shell branch.
/// Passed as the `builder` of a StatefulShellRoute.indexedStack.
class AppShell extends StatelessWidget {
  final StatefulNavigationShell navigationShell;

  const AppShell({super.key, required this.navigationShell});

  // Maps branch index -> route, matching the order branches are declared
  // in the router (Home, Lots, Scan, Review, More).
  static const List<String> _branchRoutes = [
    Screen.home,
    Screen.lots,
    Screen.scan,
    Screen.review,
    Screen.more,
  ];

  void _onNavigate(String route) {
    final index = _branchRoutes.indexOf(route);
    if (index == -1) return;
    navigationShell.goBranch(
      index,
      // Tapping the already-active tab pops it back to its root.
      initialLocation: index == navigationShell.currentIndex,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: MandiBottomNavBar(
        currentRoute: _branchRoutes[navigationShell.currentIndex],
        onNavigate: _onNavigate,
      ),
    );
  }
}