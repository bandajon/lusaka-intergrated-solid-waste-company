import 'package:flutter/material.dart';

final ThemeData appTheme = ThemeData(
  // Primary colors
  primaryColor: Color(0xFF2E7D32), // Green 800
  primaryColorLight: Color(0xFF4CAF50), // Green 500
  primaryColorDark: Color(0xFF1B5E20), // Green 900
  
  // Accent colors
  colorScheme: ColorScheme.fromSeed(
    seedColor: Color(0xFF2E7D32),
    secondary: Color(0xFFFF9800), // Orange 500
    tertiary: Color(0xFF455A64), // Blue Grey 700
  ),
  
  // Scaffolds, cards, etc.
  scaffoldBackgroundColor: Color(0xFFF5F5F5), // Grey 100
  cardTheme: CardTheme(
    elevation: 2,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    margin: EdgeInsets.zero,
  ),
  
  // Input fields
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: Colors.white,
    contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: BorderSide(color: Colors.grey.shade400),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: BorderSide(color: Colors.grey.shade400),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: BorderSide(color: Color(0xFF2E7D32), width: 2),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: BorderSide(color: Colors.red.shade700, width: 1),
    ),
  ),
  
  // Buttons
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: Color(0xFF2E7D32),
      foregroundColor: Colors.white,
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
  ),
  
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: Color(0xFF2E7D32),
      side: BorderSide(color: Color(0xFF2E7D32), width: 1.5),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
  ),
  
  textButtonTheme: TextButtonThemeData(
    style: TextButton.styleFrom(
      foregroundColor: Color(0xFF2E7D32),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
  ),
  
  // App bar
  appBarTheme: AppBarTheme(
    backgroundColor: Color(0xFF2E7D32),
    foregroundColor: Colors.white,
    elevation: 0,
    centerTitle: false,
    toolbarHeight: 60,
  ),
  
  // Typography
  textTheme: TextTheme(
    headlineLarge: TextStyle(
      fontSize: 32,
      fontWeight: FontWeight.bold,
      color: Color(0xFF212121),
    ),
    headlineMedium: TextStyle(
      fontSize: 24,
      fontWeight: FontWeight.bold,
      color: Color(0xFF212121),
    ),
    headlineSmall: TextStyle(
      fontSize: 20,
      fontWeight: FontWeight.bold,
      color: Color(0xFF212121),
    ),
    titleLarge: TextStyle(
      fontSize: 18,
      fontWeight: FontWeight.w600,
      color: Color(0xFF212121),
    ),
    titleMedium: TextStyle(
      fontSize: 16,
      fontWeight: FontWeight.w600,
      color: Color(0xFF212121),
    ),
    bodyLarge: TextStyle(
      fontSize: 16,
      color: Color(0xFF424242),
    ),
    bodyMedium: TextStyle(
      fontSize: 14,
      color: Color(0xFF424242),
    ),
  ),
  
  // Checkbox and Radio Button
  checkboxTheme: CheckboxThemeData(
    fillColor: MaterialStateProperty.resolveWith<Color>((states) {
      if (states.contains(MaterialState.selected)) {
        return Color(0xFF2E7D32);
      }
      return Colors.grey.shade400;
    }),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(3)),
  ),
  
  radioTheme: RadioThemeData(
    fillColor: MaterialStateProperty.resolveWith<Color>((states) {
      if (states.contains(MaterialState.selected)) {
        return Color(0xFF2E7D32);
      }
      return Colors.grey.shade400;
    }),
  ),
  
  // Divider
  dividerTheme: DividerThemeData(
    color: Colors.grey.shade300,
    thickness: 1.0,
    space: 24,
  ),
  
  // Progress indicator
  progressIndicatorTheme: ProgressIndicatorThemeData(
    color: Color(0xFF2E7D32),
    circularTrackColor: Colors.grey.shade200,
    linearTrackColor: Colors.grey.shade200,
  ),
  
  // Bottom navigation
  bottomNavigationBarTheme: BottomNavigationBarThemeData(
    backgroundColor: Colors.white,
    selectedItemColor: Color(0xFF2E7D32),
    unselectedItemColor: Colors.grey.shade600,
    elevation: 8,
    type: BottomNavigationBarType.fixed,
  ),
  
  // Dialog
  dialogTheme: DialogTheme(
    backgroundColor: Colors.white,
    elevation: 24,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(16),
    ),
  ),
  
  useMaterial3: true,
);