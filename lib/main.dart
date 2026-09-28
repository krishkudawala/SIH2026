import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/api/api_config.dart';
import 'package:sih2631/manid_nyaay/data/routes/app_router.dart';
import 'package:sih2631/manid_nyaay/data/theme/theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // Start 15-second backend health polling immediately on app boot.
  ApiConfig.startPeriodicHealthCheck(intervalSeconds: 15);
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'MandiProof',
      theme: AppTheme.lightTheme,
      routerConfig: AppRouter.router,
    );
  }
}