import 'package:flutter/material.dart';
import 'package:sih2631/manid_nyaay/data/theme/app_colors.dart';


class AppTheme {
  AppTheme._();

  static ThemeData get lightTheme {
    const colorScheme = ColorScheme.light(
      primary: AppColors.institutionalBlue,
      onPrimary: AppColors.textOnBlue,

      primaryContainer: AppColors.blueLight,
      onPrimaryContainer: AppColors.blueDark,

      secondary: AppColors.blueMedium,
      onSecondary: AppColors.textOnBlue,

      secondaryContainer: AppColors.blueLight,

      tertiary: AppColors.statusGreen,
      onTertiary: AppColors.textOnBlue,

      surface: AppColors.surfaceWhite,
      onSurface: AppColors.textPrimary,

      error: AppColors.statusRed,
      onError: AppColors.textOnBlue,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,

      scaffoldBackgroundColor: AppColors.backgroundGray,
      dividerColor: AppColors.dividerGray,

      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.blueDark,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
      ),

      cardTheme: CardThemeData(
        color: AppColors.cardSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: AppShapes.medium,
        ),
      ),

      dialogTheme: DialogThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: AppShapes.extraLarge,
        ),
      ),

      bottomSheetTheme: BottomSheetThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: AppShapes.large,
        ),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.institutionalBlue,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: AppShapes.medium,
          ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: AppShapes.medium,
          ),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: AppShapes.medium,
          borderSide: BorderSide(
            color: AppColors.dividerGray,
          ),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: AppShapes.medium,
          borderSide: BorderSide(
            color: AppColors.dividerGray,
          ),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: AppShapes.medium,
          borderSide: BorderSide(
            color: AppColors.institutionalBlue,
            width: 2,
          ),
        ),
      ),
    );
  }
}