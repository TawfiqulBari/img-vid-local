# Test Plan - Image-to-Video Generator

## Phase 6: Integration & Testing

**Last Updated:** January 2025
**Status:** In Progress

---

## 1. Testing Objectives

### Primary Goals
- ✅ Verify end-to-end video generation workflow
- ✅ Test both SVD and AnimateDiff pipelines
- ✅ Validate Windows ↔ WSL communication
- ✅ Ensure VRAM optimization works correctly
- ✅ Verify NSFW model integration
- ✅ Test CivitAI model browser and downloader
- ✅ Validate error handling and recovery

### Success Criteria
- All test cases pass without critical errors
- Generated videos are playable and match parameters
- VRAM stays within 12GB limit
- Path conversion works bidirectionally
- UI is responsive during generation
- Error messages are clear and actionable

---

## 2. Test Environment

### Hardware Requirements
- **GPU:** NVIDIA RTX 3060 (12GB VRAM)
- **OS:** Windows 10/11 with WSL 2
- **RAM:** 16GB+ recommended
- **Storage:** 30GB+ free space on D:\ drive

### Software Requirements
- **Windows:** .NET 6.0 Runtime
- **WSL:** Ubuntu 22.04
- **Python:** 3.10 in virtual environment
- **CUDA:** 11.8
- **Models:** SVD-XT and at least one AnimateDiff model downloaded

### Test Data
- Sample images (various formats: JPG, PNG, WebP)
- Test prompts (SFW and NSFW)
- Various resolutions (512x512, 1024x576, etc.)

---

## 3. Test Cases

### 3.1 Environment Setup Tests

#### TEST-ENV-001: WSL Environment Verification
**Objective:** Verify WSL environment is properly configured
**Steps:**
1. Run `bash scripts/setup_wsl.sh`
2. Check for errors during setup
3. Verify Python 3.10 is installed
4. Verify virtual environment is created
5. Check all dependencies are installed

**Expected Result:** Setup completes without errors

**Status:** ⏳ Pending

---

#### TEST-ENV-002: GPU Access Verification
**Objective:** Verify CUDA and GPU are accessible from WSL
**Steps:**
1. Run `python scripts/check_gpu.py`
2. Verify CUDA is available
3. Check VRAM total is ~12GB
4. Test PyTorch CUDA operations

**Expected Result:**
- CUDA available: True
- VRAM detected: ~11.9GB
- PyTorch can create tensors on GPU

**Status:** ⏳ Pending

---

#### TEST-ENV-003: Model Availability Check
**Objective:** Verify all models are downloaded correctly
**Steps:**
1. Run `python backend/generate.py --list-models`
2. Verify SVD-XT is present
3. Check at least one AnimateDiff model exists
4. Verify file sizes are correct (~2GB per model)

**Expected Result:**
- SVD-XT found
- At least 1 AnimateDiff model found
- JSON response is valid

**Status:** ⏳ Pending

---

### 3.2 Python Backend Tests

#### TEST-BACK-001: SVD Pipeline Test
**Objective:** Test SVD pipeline end-to-end
**Steps:**
1. Create test image (512x512)
2. Run: `python backend/test_generation.py --svd-only --quick`
3. Wait for generation to complete
4. Verify output video exists
5. Check video is playable

**Expected Result:**
- Video generated successfully
- 14 frames @ 8 FPS
- File size reasonable (~2-5MB)
- Video plays correctly

**Status:** ⏳ Pending

---

#### TEST-BACK-002: AnimateDiff Pipeline Test
**Objective:** Test AnimateDiff pipeline end-to-end
**Steps:**
1. Create test image (512x512)
2. Run: `python backend/test_generation.py --animatediff-only --quick`
3. Wait for generation to complete
4. Verify output video exists
5. Check video is playable

**Expected Result:**
- Video generated successfully
- 16 frames @ 16 FPS
- Prompt is applied (visible motion)
- Video plays correctly

**Status:** ⏳ Pending

---

#### TEST-BACK-003: VRAM Optimization Test
**Objective:** Verify VRAM stays within limits
**Steps:**
1. Generate video with high parameters:
   - 1024x576 resolution
   - 60 frames
   - SVD pipeline
2. Monitor VRAM usage during generation
3. Check for OOM errors

**Expected Result:**
- VRAM usage < 11.5GB
- Parameters automatically optimized if needed
- No OOM errors

**Status:** ⏳ Pending

---

#### TEST-BACK-004: Prompt Validation Test
**Objective:** Test required prompt validation
**Steps:**
1. Try generation with empty prompt
2. Try with very short prompt (2 chars)
3. Try with very long prompt (>77 tokens)
4. Try valid prompt

**Expected Result:**
- Empty prompt: Error message
- Short prompt: Error message
- Long prompt: Truncated or error
- Valid prompt: Success

**Status:** ⏳ Pending

---

### 3.3 C# Frontend Tests

#### TEST-FRONT-001: Application Launch
**Objective:** Verify application launches correctly
**Steps:**
1. Build C# application
2. Launch VideoGenerator.exe
3. Check for startup errors
4. Verify UI loads completely

**Expected Result:**
- Application starts without errors
- All UI elements visible
- Backend connection check passes

**Status:** ⏳ Pending

---

#### TEST-FRONT-002: Model List Refresh
**Objective:** Test model discovery from Python backend
**Steps:**
1. Click "Refresh Models"
2. Wait for response
3. Check dropdown populates
4. Verify model names are correct

**Expected Result:**
- Models load successfully
- SVD-XT appears
- AnimateDiff models appear
- No errors

**Status:** ⏳ Pending

---

#### TEST-FRONT-003: Image Selection
**Objective:** Test image browsing and preview
**Steps:**
1. Click "Browse Image"
2. Select a JPG file
3. Check preview displays
4. Try PNG and WebP formats

**Expected Result:**
- Image preview shows correctly
- All formats supported
- Invalid files rejected

**Status:** ⏳ Pending

---

#### TEST-FRONT-004: SVD Generation via UI
**Objective:** Full SVD generation through C# frontend
**Steps:**
1. Select SVD-XT model
2. Browse and select image
3. Enter prompt: "slow zoom in, dramatic lighting"
4. Set parameters: 25 frames, 8 FPS
5. Click "Generate Video"
6. Monitor progress
7. Check video preview loads

**Expected Result:**
- Generation starts successfully
- Progress updates appear
- Video completes without errors
- Preview plays correctly
- Output file exists at correct path

**Status:** ⏳ Pending

---

#### TEST-FRONT-005: AnimateDiff Generation via UI
**Objective:** Full AnimateDiff generation through C# frontend
**Steps:**
1. Select AnimateDiff model
2. Browse and select image
3. Enter prompt: "woman turning head, wind blowing through hair"
4. Enter negative prompt: "blurry, static"
5. Set parameters: 24 frames, 16 FPS, guidance 7.5
6. Click "Generate Video"
7. Monitor progress
8. Check video preview loads

**Expected Result:**
- Generation starts successfully
- Prompt is applied (visible in output)
- Negative prompt works
- Video completes without errors
- Preview plays correctly

**Status:** ⏳ Pending

---

#### TEST-FRONT-006: Video Player Controls
**Objective:** Test video playback controls
**Steps:**
1. Generate a video (any pipeline)
2. Click Play button
3. Click Pause button
4. Click Stop button
5. Use seek slider

**Expected Result:**
- Play/Pause/Stop work correctly
- Seek slider updates position
- Video loops or stops at end

**Status:** ⏳ Pending

---

#### TEST-FRONT-007: VRAM Stats Display
**Objective:** Test VRAM monitoring UI
**Steps:**
1. Click "Check VRAM" button
2. View statistics dialog
3. Verify values are reasonable

**Expected Result:**
- Dialog shows VRAM stats
- Total: ~11.9GB
- Available and used make sense
- Percentage calculated correctly

**Status:** ⏳ Pending

---

### 3.4 Path Conversion Tests

#### TEST-PATH-001: Windows to WSL Conversion
**Objective:** Test path conversion from C# to Python
**Steps:**
1. Select image at: `D:\Test\image.jpg`
2. Start generation
3. Check Python receives: `/mnt/d/Test/image.jpg`

**Expected Result:**
- Path converted correctly
- File found by Python backend
- No path errors

**Status:** ⏳ Pending

---

#### TEST-PATH-002: WSL to Windows Conversion
**Objective:** Test path conversion from Python to C#
**Steps:**
1. Generate video (saves to `/mnt/d/VideoGenerator/output/video_xxx.mp4`)
2. Check C# receives: `D:\VideoGenerator\output\video_xxx.mp4`
3. Verify video loads in player

**Expected Result:**
- Path converted correctly
- Video file accessible from Windows
- Preview loads successfully

**Status:** ⏳ Pending

---

### 3.5 CivitAI Integration Tests

#### TEST-CIVIT-001: Model Browser Launch
**Objective:** Test CivitAI model browser opens
**Steps:**
1. Click "🔥 Browse CivitAI Models (NSFW)"
2. Check browser window opens
3. Verify models load from catalog

**Expected Result:**
- Browser window opens
- 6 models displayed
- Details are correct

**Status:** ⏳ Pending

---

#### TEST-CIVIT-002: Model Filtering
**Objective:** Test category filtering
**Steps:**
1. Open model browser
2. Click "Photorealistic" filter
3. Click "Anime/Illustration" filter
4. Click "All Models" filter
5. Try quick recommendations

**Expected Result:**
- Filters work correctly
- Model count updates
- Recommendations highlight correct model

**Status:** ⏳ Pending

---

#### TEST-CIVIT-003: Model Download (Mock)
**Objective:** Test download functionality (without full download)
**Steps:**
1. Select a model
2. Click "Download Model"
3. Check confirmation dialog
4. **Cancel** before starting actual download

**Expected Result:**
- Confirmation shows size and NSFW level
- Cancel works correctly
- No partial files created

**Status:** ⏳ Pending

---

#### TEST-CIVIT-004: Downloaded Model Detection
**Objective:** Verify downloaded models are detected
**Steps:**
1. Manually copy a .safetensors file to `D:\VideoGenerator\models\custom\`
2. Restart application
3. Click "Refresh Models"
4. Check if custom model appears

**Expected Result:**
- Custom model detected
- Appears in dropdown as "animatediff-{name}"
- Can be selected for generation

**Status:** ⏳ Pending

---

### 3.6 Error Handling Tests

#### TEST-ERR-001: Missing Image Error
**Objective:** Test error when image is not selected
**Steps:**
1. Don't select an image
2. Enter prompt
3. Click "Generate Video"

**Expected Result:**
- Error dialog: "Please select an input image"
- Generation doesn't start

**Status:** ⏳ Pending

---

#### TEST-ERR-002: Empty Prompt Error
**Objective:** Test error when prompt is empty
**Steps:**
1. Select an image
2. Leave prompt empty
3. Click "Generate Video"

**Expected Result:**
- Error dialog: "Prompt is required"
- Generation doesn't start

**Status:** ⏳ Pending

---

#### TEST-ERR-003: Backend Unavailable Error
**Objective:** Test error when Python backend is not accessible
**Steps:**
1. Stop WSL or virtual environment
2. Launch C# application
3. Try to generate video

**Expected Result:**
- Warning on startup: "Backend not available"
- Error on generation: Clear message about backend
- Helpful instructions provided

**Status:** ⏳ Pending

---

#### TEST-ERR-004: Out of VRAM Error
**Objective:** Test VRAM exhaustion handling
**Steps:**
1. Set very high parameters (if possible):
   - 1024x1024 resolution
   - 120 frames
2. Try to generate

**Expected Result:**
- Parameters automatically optimized OR
- Clear error message about VRAM
- Suggestions for reducing usage

**Status:** ⏳ Pending

---

#### TEST-ERR-005: Cancellation Test
**Objective:** Test generation cancellation
**Steps:**
1. Start generation
2. Click "Cancel" after 5 seconds
3. Check process stops

**Expected Result:**
- Generation stops within 2-3 seconds
- Status: "Generation cancelled"
- No orphan processes
- VRAM released

**Status:** ⏳ Pending

---

### 3.7 NSFW Content Tests

#### TEST-NSFW-001: Safety Checker Disabled (SVD)
**Objective:** Verify SVD safety checker is disabled
**Steps:**
1. Use SVD pipeline
2. Use NSFW-suggestive prompt
3. Generate video

**Expected Result:**
- No safety checker filtering
- Content matches prompt
- No censorship applied

**Status:** ⏳ Pending (Manual verification)

---

#### TEST-NSFW-002: Safety Checker Disabled (AnimateDiff)
**Objective:** Verify AnimateDiff safety checker is disabled
**Steps:**
1. Use AnimateDiff pipeline
2. Use NSFW-suggestive prompt
3. Generate video

**Expected Result:**
- No safety checker filtering
- Content matches prompt
- No censorship applied

**Status:** ⏳ Pending (Manual verification)

---

#### TEST-NSFW-003: High NSFW Model Test
**Objective:** Test URPM or ChilloutMix (Level 60)
**Steps:**
1. Download URPM or ChilloutMix via browser
2. Select model in UI
3. Generate with mild prompt

**Expected Result:**
- Model generates without errors
- Output may be NSFW even with mild prompt
- Negative prompts can control output

**Status:** ⏳ Pending (Requires model download)

---

## 4. Performance Benchmarks

### Target Performance Metrics

| Pipeline | Resolution | Frames | Expected Time | VRAM Peak |
|----------|------------|--------|---------------|-----------|
| SVD | 512x512 | 25 | 30-60s | 7-8GB |
| SVD | 1024x576 | 25 | 60-90s | 9-10GB |
| AnimateDiff | 512x512 | 24 | 45-90s | 8-9GB |

### Benchmarking Tests

#### TEST-PERF-001: SVD 512x512 Benchmark
**Steps:**
1. Generate 512x512, 25 frames, SVD
2. Record time and VRAM peak
3. Compare to targets

**Status:** ⏳ Pending

---

#### TEST-PERF-002: SVD 1024x576 Benchmark
**Steps:**
1. Generate 1024x576, 25 frames, SVD
2. Record time and VRAM peak
3. Compare to targets

**Status:** ⏳ Pending

---

#### TEST-PERF-003: AnimateDiff 512x512 Benchmark
**Steps:**
1. Generate 512x512, 24 frames, AnimateDiff
2. Record time and VRAM peak
3. Compare to targets

**Status:** ⏳ Pending

---

## 5. Regression Testing Checklist

Before each release, verify:

- [ ] All environment checks pass
- [ ] Both pipelines generate successfully
- [ ] Path conversion works bidirectionally
- [ ] VRAM optimization prevents OOM errors
- [ ] UI is responsive during generation
- [ ] Video preview works
- [ ] Model browser opens and filters work
- [ ] Error messages are clear
- [ ] Cancellation works
- [ ] Documentation is up to date

---

## 6. Known Issues & Limitations

### Current Known Issues
1. **First generation slow:** Model loading takes 30-60s (expected)
2. **Kluster verification hook error:** Shell script compatibility issue (non-critical)
3. **Model discovery requires restart:** After downloading new models

### Accepted Limitations
1. **RTX 3060 only:** Designed for 12GB VRAM (other GPUs untested)
2. **WSL 2 required:** Windows-only with WSL backend
3. **Large downloads:** Models are 2GB+ each (~15GB total)
4. **First-time setup:** Requires manual model download

---

## 7. Test Execution Log

### Execution Date: _________________
### Tester: _________________
### Environment: _________________

| Test ID | Status | Notes | Issues |
|---------|--------|-------|--------|
| TEST-ENV-001 | ⏳ | | |
| TEST-ENV-002 | ⏳ | | |
| TEST-ENV-003 | ⏳ | | |
| ... | | | |

---

## 8. Sign-Off

### Testing Complete
- [ ] All critical tests passed
- [ ] Known issues documented
- [ ] Performance meets targets
- [ ] Ready for Phase 7 (Release Packaging)

**Signed:** _________________
**Date:** _________________

---

## Notes
- Tests marked ⏳ are pending execution
- Tests marked ✅ have passed
- Tests marked ❌ have failed (see issues)
- Tests marked ⚠️ require manual verification
