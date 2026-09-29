import 'package:flutter/material.dart';

/// Extension on [BuildContext] providing convenient, high-performance
/// access to [MediaQuery] dimensions, breakpoints, padding, and dynamic scaling helpers.
extension ContextMediaQueryX on BuildContext {
  /// Raw [MediaQueryData] from the current context.
  MediaQueryData get mediaQuery => MediaQuery.of(this);

  /// Total width of the current screen in logical pixels.
  double get screenWidth => mediaQuery.size.width;

  /// Total height of the current screen in logical pixels.
  double get screenHeight => mediaQuery.size.height;

  /// Total size of the screen.
  Size get screenSize => mediaQuery.size;

  /// Current device orientation (portrait or landscape).
  Orientation get orientation => mediaQuery.orientation;

  /// True if the screen is in portrait orientation.
  bool get isPortrait => orientation == Orientation.portrait;

  /// True if the screen is in landscape orientation.
  bool get isLandscape => orientation == Orientation.landscape;

  /// System padding (e.g. status bar, notch, home indicator).
  EdgeInsets get padding => mediaQuery.padding;

  /// View insets (e.g. software keyboard).
  EdgeInsets get viewInsets => mediaQuery.viewInsets;

  /// Bottom inset (e.g. height occupied by the open software keyboard).
  double get bottomInset => viewInsets.bottom;

  /// Top safe area padding (e.g. status bar height).
  double get topInset => padding.top;

  /// Device pixel ratio.
  double get devicePixelRatio => mediaQuery.devicePixelRatio;

  /// Text scale factor or text scaler value.
  double get textScaleFactor => mediaQuery.textScaler.scale(1.0);

  // ─── Screen Breakpoints ───────────────────────────────────────────

  /// True if device is a small smartphone (<360dp width).
  bool get isSmallMobile => screenWidth < 360;

  /// True if device is a standard or small mobile (<600dp width).
  bool get isMobile => screenWidth < 600;

  /// True if device is a tablet or large foldable (600dp - 1023dp width).
  bool get isTablet => screenWidth >= 600 && screenWidth < 1024;

  /// True if device is a desktop or large web screen (>=1024dp width).
  bool get isDesktop => screenWidth >= 1024;

  // ─── Dynamic Relative Sizing ───────────────────────────────────────

  /// Returns calculated width corresponding to a percentage of screen width (0..100).
  double widthPct(double percent) => screenWidth * (percent / 100);

  /// Returns calculated height corresponding to a percentage of screen height (0..100).
  double heightPct(double percent) => screenHeight * (percent / 100);

  /// Dynamically scales a font size based on device screen width/breakpoints.
  double responsiveFontSize(double baseSize) {
    if (isSmallMobile) return baseSize * 0.88;
    if (isTablet) return baseSize * 1.15;
    if (isDesktop) return baseSize * 1.30;
    return baseSize;
  }

  /// Dynamically scales spacing/padding based on screen size.
  double responsivePadding(double basePadding) {
    if (isSmallMobile) return basePadding * 0.85;
    if (isTablet) return basePadding * 1.25;
    if (isDesktop) return basePadding * 1.5;
    return basePadding;
  }
}

/// A responsive layout builder that picks different widgets depending on the device width.
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget? desktop;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
    this.desktop,
  });

  @override
  Widget build(BuildContext context) {
    if (context.isDesktop && desktop != null) {
      return desktop!;
    }
    if (context.isTablet && tablet != null) {
      return tablet!;
    }
    return mobile;
  }
}
