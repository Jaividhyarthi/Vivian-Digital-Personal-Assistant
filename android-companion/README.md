# Vivian Android Companion v0.1

Native Kotlin Android application for Vivian Personal AI.

## Current features
- Shows phone manufacturer, model, Android version and local-only status.
- Opens supported installed apps when the owner taps a button.
- Links to Android notification-access and accessibility settings for future development.
- No network permissions, no background service, no accessibility service, no notification listener, no remote commands, and no sensitive data collection.

## Build
1. Open the `android-companion` folder as a project in Android Studio (JDK 17).
2. Let Android Studio sync Gradle and install Android SDK 35 if prompted.
3. Choose **Build > Build APK(s)**.
4. Find the debug APK under `app/build/outputs/apk/debug/`.
5. Install on your Android phone using a trusted transfer mechanism. Android may ask you to allow installation from that source.

The project intentionally does not commit a Gradle wrapper JAR. Android Studio can use an installed Gradle distribution compatible with Android Gradle Plugin 8.9.2. If Gradle sync fails, configure Gradle 8.11.1 in Android Studio.

## Next milestones
1. Explicit local device pairing with short-lived challenge and scoped authorization.
2. Local command executor with an allowlist, audit log, and user confirmation.
3. Notification listener with opt-in and sensitive-content filtering.
4. Foreground voice interaction.
5. Accessibility automation only where supported, permitted, and user-authorized.

Never place API keys, personal exports, device tokens, or private data in this public repository. A Codespaces preview is not an always-on or trusted phone-control endpoint.
