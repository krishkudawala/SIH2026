import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/bottom_nav_bar.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/ScanScreen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/home/home_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/lots/lots_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/review/review_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/more/more_screen.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int selectedIndex = 0;

  // ✅ Order matches bottom nav: Home, Lots, Scan, Review, More
  static const List<String> _routes = [
    '/home',   // 0
    '/lots',   // 1
    '/scan',   // 2  👈 ScanScreen (camera)
    '/review', // 3
    '/more',   // 4
  ];

  final List<Widget> pages = const [
    HomeScreen(),      // 0
    LotsScreen(),      // 1
    ScanScreen(),      // 2  👈 Camera + scan → phir khud navigates to InspectionScreen
    ReviewScreen(),    // 3
    MoreScreen(),      // 4
  ];

  void _onNavigate(String route) {
    debugPrint('🧭 Tapped: $route → index ${_routes.indexOf(route)}');
    final index = _routes.indexOf(route);
    if (index == -1 || index == selectedIndex) return;
    setState(() {
      selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: selectedIndex,
        children: pages,
      ),
      bottomNavigationBar: MandiBottomNavBar(
        currentRoute: _routes[selectedIndex],
        onNavigate: _onNavigate,
      ),
    );
  }
}