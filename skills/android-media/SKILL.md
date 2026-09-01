---
name: android-media
description: >
  Add camera (CameraX) and/or media playback (Media3 ExoPlayer) to an
  Android app. Use this when the user said "yes" to camera, microphone,
  video, or music during /make-app, or asks to add photo/video capture or
  audio/video playback. Do not use for image loading (use Coil), video
  editing, or streaming protocols.
license: Apache-2.0
metadata:
  author: Mitun
  last-updated: '2026-09-01'
  keywords: [camerax, media3, exoplayer, camera, video, audio]
---

# Android Media

> [!NOTE]
> CameraX for capture. Media3 ExoPlayer for playback. Add only what the spec asks for.

## Prerequisites

- A scaffolded project
- Camera/audio permissions declared in `AndroidManifest.xml`

## Workflow

### Step 1: Read the spec

Read `.build-android/spec.md` for `media` field. Possible values:

- `None` → exit
- `Camera only` → CameraX (preview + capture)
- `Microphone only` → MediaRecorder + visualizer
- `Camera + microphone` → CameraX + AudioRecord (video recording)
- `Music playback` → Media3 ExoPlayer
- `Video playback` → Media3 ExoPlayer (PlayerView)

### Step 2: Permissions

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-feature android:name="android.hardware.camera" android:required="false" />
```

Runtime permission request via `rememberLauncherForActivityResult` + `RequestPermission`.

### Step 3: CameraX preview + capture

```kotlin
@Composable
fun CameraPreview(onCaptured: (Uri) -> Unit) {
    val ctx = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val previewView = remember { PreviewView(ctx) }
    val controller = remember { LifecycleCameraController(ctx).apply {
        bindToLifecycle(lifecycleOwner)
        setEnabledUseCases(Controller.PREVIEW or Controller.IMAGE_CAPTURE)
    } }
    AndroidView(factory = { previewView }, update = { it.controller = controller })
    Button(onClick = {
        controller.takePicture(ctx.contentResolver,
            MediaStoreOutputOptions.Builder().setContentValues(...).build(),
            ctx.mainExecutor,
            object : OnImageCapturedCallback() {
                override fun onCaptureSuccess(output: ImageCaptureOutput) { onCaptured(output.savedUri!!) }
            })
    }) { Text("Capture") }
}
```

### Step 4: Media3 ExoPlayer

```kotlin
val player = remember { ExoPlayer.Builder(ctx).build() }
LaunchedEffect(uri) {
    player.setMediaItem(MediaItem.fromUri(uri))
    player.prepare()
    player.playWhenReady = true
}
DisposableEffect(player) { onDispose { player.release() } }

AndroidView(factory = { PlayerView(ctx).apply { this.player = player } })
```

### Step 5: Cleanup

Always release ExoPlayer in `DisposableEffect.onDispose`. Don't leak.

## Anti-patterns

- **DO NOT** call `CameraController.startCamera()` on a Composable without `bindToLifecycle`.
- **DO NOT** skip runtime permission requests. A `SecurityException` will crash the app.
- **DO NOT** forget to release `ExoPlayer`. Memory leak.
- **DO NOT** use the deprecated `MediaPlayer`. Use `Media3 ExoPlayer`.

## Pairing

- `android-backend` — upload captured media to storage (Supabase/Firebase)

## References

- See [references/camerax-vs-camera2.md](references/camerax-vs-camera2.md)
  for when to drop down to Camera2 (rare; usually CameraX suffices).
