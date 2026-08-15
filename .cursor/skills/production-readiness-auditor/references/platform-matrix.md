# Platform matrix и инструментальная стратегия

Выбирать инструменты **после** discovery. Варианты ниже — не обязательные зависимости. Перед использованием проверить наличие и версию. Не устанавливать глобальные tools автоматически. Не выдумывать, что инструмент установлен.

## Общий алгоритм выбора

1. Прочитать CI workflows и project scripts — использовать их первыми.
2. Запустить `scripts/detect-project.py` → список detected platforms.
3. Для каждой платформы проверить toolchain (`xcodebuild -version`, `adb version`, `flutter --version`, …).
4. Если toolchain отсутствует → проверка `BLOCKED`, зафиксировать что нужно.
5. Предпочитать официальные/уже подключённые runners проекта.
6. UI automation — только если драйвер доступен или пользователь разрешил установку в изолированное окружение.

## iOS / iPadOS

| Область | Кандидаты | Примечания |
|---------|-----------|------------|
| Build | `xcodebuild`, XcodeGen, Tuist, SPM | Schemes/configurations из проекта |
| Unit/UI | XCTest, XCUITest | Не путать simulator и device |
| Devices | `xcrun simctl`, physical device | Signing/provisioning могут BLOCKED |
| Perf | Instruments, `xctrace` | Release-like build предпочтителен |
| A11y | Accessibility Inspector, XCUI accessibility APIs | |
| Packages | `.ipa`, Archive, App Store Connect metadata | Не выгружать без разрешения |

Сигналы репозитория: `*.xcodeproj`, `*.xcworkspace`, `Project.swift`, `project.yml`, `Package.swift`, `*.swift`.

## macOS desktop

| Область | Кандидаты |
|---------|-----------|
| Native | SwiftUI/AppKit + `xcodebuild`, XCTest |
| Electron | project `package.json` scripts, Playwright/Spectron-replacement/Appium при наличии |
| Qt | CMake/qmake, Qt Test, platform automation |
| Flutter / Tauri | `flutter` / `cargo` + project scripts |
| Packages | `.app`, DMG, PKG, notarization status (check only) |

## Android

| Область | Кандидаты | Примечания |
|---------|-----------|------------|
| Build | Gradle (`./gradlew`), AGP | flavors/buildTypes |
| Unit | JUnit, Robolectric | |
| UI | Espresso, Compose UI Test, UI Automator | |
| Devices | `adb`, emulator | |
| Perf | Macrobenchmark, Baseline Profiles, Android Profiler, Perfetto | |
| Packages | APK/AAB, bundletool | signing configs без утечки keystore |

Сигналы: `build.gradle`, `build.gradle.kts`, `settings.gradle*`, `AndroidManifest.xml`.

## Flutter

| Область | Кандидаты |
|---------|-----------|
| Analyze/test | `flutter analyze`, `flutter test` |
| Integration | `integration_test`, device/desktop targets |
| Perf/UI | Flutter DevTools, timeline |
| Multi-platform | отдельно iOS/Android/desktop/web если в scope |

Сигналы: `pubspec.yaml`, `lib/main.dart`.

## React Native

| Область | Кандидаты |
|---------|-----------|
| JS tests | Jest / project scripts |
| E2E | Detox, Maestro, Appium — **если уже в проекте** |
| Native | iOS/Android toolchains как выше |
| Metro/build | project scripts, not guessed globals |

Сигналы: `react-native`, `app.json`, `metro.config.*`, `ios/` + `android/`.

## Windows desktop

| Стек | Build/test | UI / package |
|------|------------|--------------|
| .NET / WPF / WinUI / MAUI | `dotnet build`, `dotnet test` | WinAppDriver/Appium при наличии; MSIX tooling |
| Electron | npm/pnpm/yarn scripts | Playwright и т.п. при наличии |
| Qt | CMake/qmake, Qt Test | |
| Flutter / Tauri | flutter/cargo scripts | MSIX/EXE/MSI validation |
| Perf | Windows Performance Recorder/Toolkit если доступны | |

## Linux desktop

| Стек | Кандидаты |
|------|-----------|
| Qt / GTK | project CMake/meson/autotools; Qt Test |
| Electron / Flutter / Tauri | project scripts |
| Packages | AppImage, deb, rpm, Flatpak, Snap — validate metadata; не публиковать |

Headless CI может ограничить GUI → `BLOCKED` для интерактивных UI checks с указанием потребности в display/device.

## Кроссплатформа / monorepo

- Обнаружить workspaces (npm/pnpm/yarn, Cargo workspace, Gradle composite, Tuist, Melos, Bazel и т.д.).
- Аудит scope: либо все app packages, либо явно выбранные пользователем.
- Shared libraries: regression impact analysis при изменениях.
- Не запускать все платформы «наугад» — матрица из detect + supported platforms docs.

## Backend / API / realtime (если часть продукта)

| Область | Кандидаты |
|---------|-----------|
| Contract/tests | существующие pytest/Jest/Go test и т.д. |
| Load | сначала project tools; иначе k6/JMeter/Locust **только при наличии или с разрешения** |
| Health | `/health`, readiness, project probes |
| WS/push | тестовый стенд; не долбить production |

Нагрузка и destructive security — **только** local/test/explicitly allowed stand.

## Security scanners (порядок)

1. Уже настроенные в CI (CodeQL, Semgrep, Dependabot, Snyk, OSVи т.д.).
2. Language-native: `npm audit`, `pip-audit`, `gradle` dependency check, `cargo audit`, `bundle audit` — если доступны.
3. Secret scan: gitleaks/trufflehog/project tool — если доступны; иначе осторожный pattern search **без** печати секретов.
4. Не заявлять OWASP certification; использовать MASVS/MSTG/ASVS как **чеклист**.

## UI automation drivers (опционально)

| Платформа | Возможные драйверы |
|-----------|-------------------|
| iOS/macOS | XCUITest |
| Android | Espresso / Compose / UI Automator |
| Cross | Appium, Maestro |
| Electron | Playwright |
| Windows | WinAppDriver / Appium |
| Fallback | Ручной протокол из [evidence-policy.md](evidence-policy.md) |

Если драйвера нет — `BLOCKED`/`NOT RUN` для automated UI, продолжить manual sample + static.

## Проверка доступности toolchain (примеры)

```bash
command -v xcodebuild && xcodebuild -version
command -v adb && adb version
command -v flutter && flutter --version
command -v dotnet && dotnet --version
command -v node && node --version
command -v cargo && cargo --version
command -v cmake && cmake --version
```

Фиксировать в manifest: tool, version, path, или `missing`.
