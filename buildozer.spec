[app]
title = Sudoku 1-5 100 Levels
package.name = sudoku15levels
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,kv,atlas,json
version = 1.1.0
presplash.filename = assets/presplash.png
requirements = python3,kivy
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.accept_sdk_license = True
# Buildozer can use sensible defaults. Set these if your build environment requires them.
# android.api = 35
# android.minapi = 23
# android.archs = arm64-v8a, armeabi-v7a
