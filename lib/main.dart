import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/routes/app_router.dart';
import 'package:sih2631/manid_nyaay/data/theme/theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'Mandi Nyaay',
      theme: AppTheme.lightTheme,
      routerConfig: AppRouter.router,
    );
  }
}