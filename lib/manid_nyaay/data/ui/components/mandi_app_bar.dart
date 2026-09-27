import 'package:flutter/material.dart';

// Note: Replace these with your actual theme colors
// equivalent to your com.mandiNyaay.ui.theme colors
const Color blueDark = Color(0xFF0F2B46); // Placeholder
const Color textOnBlue = Colors.white;
const Color blueMedium = Colors.blueAccent;

class MandiTopAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final String? subtitle;
  final bool showBack;
  final bool showNotifications;
  final bool showAvatar;
  final String avatarInitials;
  final VoidCallback? onBack;
  final VoidCallback? onNotifications;
  final VoidCallback? onAvatar;

  const MandiTopAppBar({
    super.key,
    required this.title,
    this.subtitle,
    this.showBack = false,
    this.showNotifications = false,
    this.showAvatar = false,
    this.avatarInitials = "RS",
    this.onBack,
    this.onNotifications,
    this.onAvatar,
  });

  // Implements PreferredSizeWidget so you can use it in Scaffold(appBar: ...)
  @override
  Size get preferredSize => const Size.fromHeight(64.0);

  @override
  Widget build(BuildContext context) {
    // Material perfectly replicates Compose's Surface
    return Material(
      color: blueDark,
      elevation: 4.0, // shadowElevation
      child: SafeArea(
        bottom: false, // Replicates statusBarsPadding()
        child: Container(
          height: 64.0,
          padding: const EdgeInsets.symmetric(horizontal: 8.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center, // verticalAlignment = Alignment.CenterVertically
            children: [
              // Back Button or Spacer
              if (showBack)
                IconButton(
                  icon: const Icon(Icons.arrow_back), // Auto-mirrored natively in Flutter
                  color: textOnBlue,
                  onPressed: onBack,
                )
              else
                const SizedBox(width: 8.0),

              // Title and Subtitle Column
              Expanded( // Modifier.weight(1f)
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: textOnBlue,
                        fontWeight: FontWeight.w800, // ExtraBold
                        letterSpacing: -0.5,
                      ),
                    ),
                    if (subtitle != null)
                      Text(
                        subtitle!,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: textOnBlue.withOpacity(0.8),
                          fontWeight: FontWeight.w500, // Medium
                        ),
                      ),
                  ],
                ),
              ),

              // Notifications Button
              if (showNotifications)
                IconButton(
                  icon: const Icon(Icons.notifications),
                  color: textOnBlue,
                  onPressed: onNotifications,
                ),

              // Avatar Button
              if (showAvatar)
                Padding(
                  padding: const EdgeInsets.only(right: 8.0),
                  child: Material(
                    shape: const CircleBorder(), // Modifier.clip(CircleShape)
                    color: blueMedium, // Modifier.background(BlueMedium)
                    clipBehavior: Clip.antiAlias,
                    child: InkWell(
                      onTap: onAvatar, // Modifier.clickable
                      child: SizedBox(
                        width: 36.0,
                        height: 36.0,
                        child: Center(
                          child: Text(
                            avatarInitials,
                            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              color: textOnBlue,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}