#!/bin/bash
##############################################################################
# Integration Test Script
##############################################################################
#
# Runs comprehensive integration tests for the Image-to-Video Generator
#
# Usage:
#   bash scripts/test_integration.sh
#   bash scripts/test_integration.sh --quick    # Quick test with minimal frames
#   bash scripts/test_integration.sh --full     # Full test with all features
#
##############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${BLUE}TEST:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

print_skip() {
    echo -e "${YELLOW}⏭️  SKIP:${NC} $1"
    ((TESTS_SKIPPED++))
}

print_info() {
    echo -e "ℹ️  $1"
}

# Parse arguments
QUICK_MODE=false
FULL_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --full)
            FULL_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--quick|--full]"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_header "Integration Test Suite"
print_info "Project root: $PROJECT_ROOT"
print_info "Mode: $([ "$QUICK_MODE" = true ] && echo "Quick" || echo "Standard")"

##############################################################################
# Test 1: Environment Verification
##############################################################################

print_header "Test 1: Environment Verification"

print_test "Running verify_setup.py"

if python "$PROJECT_ROOT/backend/verify_setup.py"; then
    print_success "Environment verification passed"
else
    print_error "Environment verification failed"
    print_info "Fix environment issues before continuing"
    exit 1
fi

##############################################################################
# Test 2: Python Backend - Model Discovery
##############################################################################

print_header "Test 2: Model Discovery"

print_test "List available models"

MODELS_OUTPUT=$(python "$PROJECT_ROOT/backend/generate.py" --list-models 2>&1)

if echo "$MODELS_OUTPUT" | grep -q '"success": *true'; then
    MODEL_COUNT=$(echo "$MODELS_OUTPUT" | grep -o '"count": *[0-9]*' | grep -o '[0-9]*')
    print_success "Model discovery successful ($MODEL_COUNT models found)"
else
    print_error "Model discovery failed"
    print_info "Output: $MODELS_OUTPUT"
fi

##############################################################################
# Test 3: Python Backend - VRAM Stats
##############################################################################

print_header "Test 3: VRAM Statistics"

print_test "Get VRAM statistics"

VRAM_OUTPUT=$(python "$PROJECT_ROOT/backend/generate.py" --vram-stats 2>&1)

if echo "$VRAM_OUTPUT" | grep -q '"success": *true'; then
    print_success "VRAM statistics retrieved"

    # Extract VRAM values
    TOTAL_VRAM=$(echo "$VRAM_OUTPUT" | grep -o '"total_gb": *[0-9.]*' | grep -o '[0-9.]*')
    if [ ! -z "$TOTAL_VRAM" ]; then
        print_info "Total VRAM: ${TOTAL_VRAM}GB"
    fi
else
    print_error "VRAM statistics failed"
fi

##############################################################################
# Test 4: Path Conversion
##############################################################################

print_header "Test 4: Path Conversion (Python)"

print_test "Windows to WSL path conversion"

# Test via Python
PYTHON_TEST=$(python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/backend')
from utils.path_utils import windows_to_wsl_path, wsl_to_windows_path

# Test Windows to WSL
result1 = windows_to_wsl_path('D:\\\\VideoGenerator\\\\models')
expected1 = '/mnt/d/VideoGenerator/models'

# Test WSL to Windows
result2 = wsl_to_windows_path('/mnt/d/VideoGenerator/models')
expected2 = 'D:\\\\VideoGenerator\\\\models'

if result1 == expected1 and result2 == expected2:
    print('PASS')
else:
    print(f'FAIL: {result1} != {expected1} or {result2} != {expected2}')
")

if echo "$PYTHON_TEST" | grep -q "PASS"; then
    print_success "Path conversion working correctly"
else
    print_error "Path conversion failed: $PYTHON_TEST"
fi

##############################################################################
# Test 5: Prompt Validation
##############################################################################

print_header "Test 5: Prompt Validation"

print_test "Empty prompt validation"

PYTHON_PROMPT_TEST=$(python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/backend')
from utils.prompt_utils import PromptValidator

validator = PromptValidator()

# Test empty prompt
is_valid, error = validator.validate_prompt('')
if not is_valid and error:
    print('PASS')
else:
    print('FAIL: Empty prompt should fail validation')

# Test valid prompt
is_valid, error = validator.validate_prompt('slow cinematic zoom in')
if is_valid:
    print('PASS')
else:
    print('FAIL: Valid prompt should pass validation')
")

PASS_COUNT=$(echo "$PYTHON_PROMPT_TEST" | grep -c "PASS" || echo "0")

if [ "$PASS_COUNT" = "2" ]; then
    print_success "Prompt validation working correctly"
else
    print_error "Prompt validation failed"
fi

##############################################################################
# Test 6: Quick Video Generation (SVD)
##############################################################################

if [ "$QUICK_MODE" = false ]; then
    print_header "Test 6: SVD Video Generation (Quick)"

    print_test "Generate test video with SVD"
    print_info "This may take 30-90 seconds..."

    if python "$PROJECT_ROOT/backend/test_generation.py" --svd-only --quick 2>&1 | tee /tmp/svd_test.log; then
        # Check if video was generated
        if ls /mnt/d/VideoGenerator/output/*.mp4 1> /dev/null 2>&1; then
            LATEST_VIDEO=$(ls -t /mnt/d/VideoGenerator/output/*.mp4 | head -1)
            VIDEO_SIZE=$(du -h "$LATEST_VIDEO" | cut -f1)
            print_success "SVD generation successful (Size: $VIDEO_SIZE)"
            print_info "Output: $LATEST_VIDEO"
        else
            print_error "SVD generation failed: No output video found"
        fi
    else
        print_error "SVD generation failed: Script error"
    fi
else
    print_skip "SVD generation test (use without --quick for full test)"
fi

##############################################################################
# Test 7: AnimateDiff Video Generation
##############################################################################

if [ "$FULL_MODE" = true ]; then
    print_header "Test 7: AnimateDiff Video Generation"

    print_test "Generate test video with AnimateDiff"
    print_info "This may take 45-120 seconds..."

    if python "$PROJECT_ROOT/backend/test_generation.py" --animatediff-only --quick 2>&1 | tee /tmp/animatediff_test.log; then
        # Count videos generated
        VIDEO_COUNT=$(ls /mnt/d/VideoGenerator/output/*.mp4 2>/dev/null | wc -l)
        if [ "$VIDEO_COUNT" -ge 2 ]; then
            print_success "AnimateDiff generation successful"
        else
            print_error "AnimateDiff generation may have failed"
        fi
    else
        print_error "AnimateDiff generation failed: Script error"
    fi
else
    print_skip "AnimateDiff generation test (use --full for complete test)"
fi

##############################################################################
# Test 8: CLI Generation with JSON
##############################################################################

if [ "$FULL_MODE" = true ]; then
    print_header "Test 8: CLI Generation with JSON Parameters"

    print_test "Generate video via CLI with JSON params"

    # Create temporary test image
    TEST_IMAGE="/tmp/test_image_$$.jpg"
    python -c "
from PIL import Image
import numpy as np
img = Image.fromarray(np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8))
img.save('$TEST_IMAGE')
"

    JSON_PARAMS=$(cat <<EOF
{
    "image_path": "$TEST_IMAGE",
    "prompt": "test generation, slow zoom in",
    "model_name": "svd-xt",
    "num_frames": 14,
    "fps": 8,
    "width": 512,
    "height": 512,
    "seed": 42
}
EOF
)

    RESULT=$(python "$PROJECT_ROOT/backend/generate.py" "$JSON_PARAMS" 2>&1)

    if echo "$RESULT" | grep -q '"success": *true'; then
        print_success "CLI JSON generation successful"
    else
        print_error "CLI JSON generation failed"
        print_info "Output: $(echo "$RESULT" | head -20)"
    fi

    # Cleanup
    rm -f "$TEST_IMAGE"
else
    print_skip "CLI JSON generation test (use --full for complete test)"
fi

##############################################################################
# Test 9: C# Build Test
##############################################################################

print_header "Test 9: C# Project Build"

print_test "Build C# WPF application"

if command -v dotnet &> /dev/null; then
    cd "$PROJECT_ROOT/VideoGenerator"

    if dotnet build --configuration Release > /tmp/csharp_build.log 2>&1; then
        print_success "C# build successful"

        # Check output exists
        if [ -f "bin/Release/net6.0-windows/VideoGenerator.dll" ]; then
            print_info "Executable: VideoGenerator/bin/Release/net6.0-windows/VideoGenerator.exe"
        fi
    else
        print_error "C# build failed"
        print_info "See: /tmp/csharp_build.log"
    fi

    cd "$PROJECT_ROOT"
else
    print_skip "C# build test (.NET SDK not found)"
fi

##############################################################################
# Test 10: Output Directory Check
##############################################################################

print_header "Test 10: Output Directory Check"

print_test "Check output directory and videos"

if [ -d "/mnt/d/VideoGenerator/output" ]; then
    VIDEO_COUNT=$(ls /mnt/d/VideoGenerator/output/*.mp4 2>/dev/null | wc -l)
    if [ "$VIDEO_COUNT" -gt 0 ]; then
        print_success "Output directory contains $VIDEO_COUNT video(s)"

        # Show latest video info
        LATEST=$(ls -t /mnt/d/VideoGenerator/output/*.mp4 | head -1)
        SIZE=$(du -h "$LATEST" | cut -f1)
        print_info "Latest: $(basename "$LATEST") ($SIZE)"
    else
        print_info "Output directory exists but contains no videos"
    fi
else
    print_error "Output directory not found: /mnt/d/VideoGenerator/output"
fi

##############################################################################
# Summary
##############################################################################

print_header "Test Summary"

echo -e "${GREEN}Passed:${NC}  $TESTS_PASSED"
echo -e "${RED}Failed:${NC}  $TESTS_FAILED"
echo -e "${YELLOW}Skipped:${NC} $TESTS_SKIPPED"

TOTAL=$((TESTS_PASSED + TESTS_FAILED))
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL))
    echo -e "\nSuccess Rate: ${SUCCESS_RATE}%"
fi

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed! 🎉${NC}\n"
    echo "Next steps:"
    echo "  1. Run full test: bash scripts/test_integration.sh --full"
    echo "  2. Test C# application manually"
    echo "  3. Proceed to Phase 7 (Release Packaging)"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Please review the errors above.${NC}\n"
    exit 1
fi
