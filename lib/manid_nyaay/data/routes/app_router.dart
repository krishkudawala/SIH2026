import 'package:go_router/go_router.dart';
import 'package:sih2631/manid_nyaay/main_screen.dart';
import 'package:sih2631/manid_nyaay/splash_screen.dart';
import 'package:sih2631/manid_nyaay/data/routes/route_paths.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/lots/lots_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/lots/lots_details_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/lots/new_lot_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/review/review_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/more/more_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/profile/profile_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/reports/reports_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/sync/offline_sync_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/inspection/inspection_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/result/grading_result_screen.dart';
import 'package:sih2631/manid_nyaay/data/ui/screens/farmer/farmer_details_screen.dart';

class AppRouter {
  static final router = GoRouter(
    initialLocation: RoutePaths.splash,
    routes: [
      GoRoute(
        path: RoutePaths.splash,
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: RoutePaths.home,
        builder: (context, state) => const MainScreen(),
      ),
      GoRoute(
        path: RoutePaths.lots,
        builder: (context, state) => const LotsScreen(),
      ),
      GoRoute(
        path: RoutePaths.review,
        builder: (context, state) => const ReviewScreen(),
      ),
      GoRoute(
        path: RoutePaths.more,
        builder: (context, state) => const MoreScreen(),
      ),
      GoRoute(
        path: RoutePaths.newLot,
        builder: (context, state) => const NewLotScreen(),
      ),
      GoRoute(
        path: RoutePaths.lotDetails,
        builder: (context, state) {
          final lotId = state.pathParameters['lotId'] ?? '';
          return LotDetailsScreen(lotId: lotId);
        },
      ),
      GoRoute(
        path: RoutePaths.inspection,
        builder: (context, state) {
          final lotId = state.pathParameters['lotId'] ?? '';
          return InspectionScreen(lotId: lotId);
        },
      ),
      GoRoute(
        path: RoutePaths.gradingResult,
        builder: (context, state) {
          final lotId = state.pathParameters['lotId'] ?? '';
          return GradingResultScreen(lotId: lotId);
        },
      ),
      GoRoute(
        path: RoutePaths.farmerDetails,
        builder: (context, state) {
          final farmerId = state.pathParameters['farmerId'] ?? '';
          return FarmerDetailsScreen(farmerId: farmerId);
        },
      ),
      GoRoute(
        path: RoutePaths.profile,
        builder: (context, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: RoutePaths.reports,
        builder: (context, state) => const ReportsScreen(),
      ),
      GoRoute(
        path: RoutePaths.offlineSync,
        builder: (context, state) => const OfflineSyncScreen(),
      ),
    ],
  );
}
