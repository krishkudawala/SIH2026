import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/AppShell.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/ScanScreen.dart';
import 'package:sih2631/manid_nyaay/splash_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/navigation/screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/sync/offline_sync_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/farmer/farmer_details_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/home/home_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/lots/lots_details_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/lots/lots_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/lots/new_lot_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/more/more_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/profile/profile_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/reports/reports_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/result/grading_result_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/review/review_screen.dart';


final GoRouter mandiNyaayNavGraph = GoRouter(
  initialLocation: Screen.splash,
  routes: [
    GoRoute(
      path: Screen.splash,
      builder: (context, state) => const SplashScreen(),
    ),

    // ── Bottom nav shell: keeps AppShell + bottom nav bar mounted while
    //    switching between the 5 tabs, each with its own nav stack ──────────
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) =>
          AppShell(navigationShell: navigationShell),
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: Screen.home,
              builder: (context, state) => const HomeScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: Screen.lots,
              builder: (context, state) => const LotsScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: Screen.scan,
              builder: (context, state) => const ScanScreen(
              ),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: Screen.review,
              builder: (context, state) => const ReviewScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: Screen.more,
              builder: (context, state) => const MoreScreen(),
            ),
          ],
        ),
      ],
    ),

    // ── Secondary destinations (pushed full-screen, outside the shell) ──────
    GoRoute(
      path: Screen.newLot,
      builder: (context, state) => const NewLotScreen(),
    ),
    GoRoute(
      path: Screen.lotDetails,
      builder: (context, state) {
        final lotId = state.pathParameters['lotId'] ?? '';
        return LotDetailsScreen(lotId: lotId);
      },
    ),
    GoRoute(
      path: Screen.inspection,
      builder: (context, state) {
        final lotId = state.pathParameters['lotId'] ?? '';
        return InspectionScreen(lotId: lotId);
      },
    ),
    GoRoute(
      path: Screen.gradingResult,
      builder: (context, state) {
        final lotId = state.pathParameters['lotId'] ?? '';
        return GradingResultScreen(lotId: lotId);
      },
    ),
    GoRoute(
      path: Screen.farmerDetails,
      builder: (context, state) {
        final farmerId = state.pathParameters['farmerId'] ?? '';
        return FarmerDetailsScreen(farmerId: farmerId);
      },
    ),
    GoRoute(
      path: Screen.profile,
      builder: (context, state) => const ProfileScreen(),
    ),
    GoRoute(
      path: Screen.reports,
      builder: (context, state) => const ReportsScreen(),
    ),
    GoRoute(
      path: Screen.offlineSync,
      builder: (context, state) => const OfflineSyncScreen(),
    ),
  ],
);