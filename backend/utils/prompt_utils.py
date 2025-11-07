"""
Prompt Utilities for Text-Guided Video Generation

Handles prompt validation, enhancement, and token counting
Prompts are REQUIRED for all generations in this application
"""

import re
from typing import Tuple, Optional, List


class PromptValidator:
    """Validate and process prompts for video generation"""

    # Maximum tokens for CLIP text encoder (SD 1.5 / SVD)
    MAX_TOKENS = 77

    # Minimum meaningful prompt length
    MIN_PROMPT_LENGTH = 3

    # Common quality/style tags that can enhance prompts
    QUALITY_TAGS = [
        "masterpiece", "best quality", "high quality", "highly detailed",
        "8k", "4k", "ultra detailed", "cinematic", "professional"
    ]

    # Common negative prompt tags
    COMMON_NEGATIVE = [
        "blurry", "low quality", "distorted", "ugly", "deformed",
        "bad anatomy", "static", "worst quality", "low res"
    ]

    def __init__(self):
        """Initialize prompt validator"""
        pass

    def validate_prompt(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """
        Validate prompt for video generation

        Args:
            prompt: User prompt string

        Returns:
            Tuple of (is_valid, error_message)
            error_message is None if valid
        """
        # Check if prompt exists
        if not prompt or not prompt.strip():
            return False, "Prompt is required and cannot be empty"

        # Check minimum length
        if len(prompt.strip()) < self.MIN_PROMPT_LENGTH:
            return False, f"Prompt too short (minimum {self.MIN_PROMPT_LENGTH} characters)"

        # Check for potentially problematic characters
        if prompt.count('"') % 2 != 0:
            return False, "Unmatched quotation marks in prompt"

        # Check token count (approximate)
        tokens = self.estimate_token_count(prompt)
        if tokens > self.MAX_TOKENS:
            return False, f"Prompt too long ({tokens} tokens, maximum {self.MAX_TOKENS})"

        return True, None

    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for CLIP tokenizer

        This is an approximation. Actual tokenization may vary slightly.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Simple estimation: split by spaces and punctuation
        # CLIP tokenizer is roughly 1.3 tokens per word on average
        words = len(text.split())
        return int(words * 1.3)

    def truncate_prompt(self, prompt: str, max_tokens: int = None) -> str:
        """
        Truncate prompt to fit within token limit

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens (default: self.MAX_TOKENS)

        Returns:
            Truncated prompt
        """
        if max_tokens is None:
            max_tokens = self.MAX_TOKENS

        estimated = self.estimate_token_count(prompt)

        if estimated <= max_tokens:
            return prompt

        # Truncate by words
        words = prompt.split()
        # Target ~0.77 words per token (inverse of 1.3 tokens per word)
        target_words = int(max_tokens * 0.77)

        truncated = ' '.join(words[:target_words])
        return truncated + "..."

    def enhance_prompt(
        self,
        prompt: str,
        add_quality_tags: bool = False,
        pipeline: str = "svd"
    ) -> str:
        """
        Enhance prompt with recommended additions

        Args:
            prompt: Original prompt
            add_quality_tags: Whether to add quality tags
            pipeline: Pipeline type ("svd" or "animatediff")

        Returns:
            Enhanced prompt
        """
        enhanced = prompt.strip()

        if add_quality_tags and pipeline == "animatediff":
            # Only add quality tags for AnimateDiff (stronger text conditioning)
            # Don't add for SVD (limited text conditioning)
            if not any(tag in enhanced.lower() for tag in self.QUALITY_TAGS):
                enhanced = f"{enhanced}, masterpiece, best quality, highly detailed"

        return enhanced

    def get_default_negative_prompt(self, pipeline: str = "svd") -> str:
        """
        Get recommended default negative prompt

        Args:
            pipeline: Pipeline type

        Returns:
            Default negative prompt
        """
        if pipeline == "animatediff":
            return "blurry, distorted, low quality, static, ugly, deformed, bad anatomy, worst quality, low res"
        else:
            # SVD has limited negative prompt support
            return "blurry, low quality, distorted"

    def split_long_prompt(self, prompt: str, max_tokens: int = None) -> List[str]:
        """
        Split long prompt into multiple chunks

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens per chunk

        Returns:
            List of prompt chunks
        """
        if max_tokens is None:
            max_tokens = self.MAX_TOKENS

        estimated = self.estimate_token_count(prompt)

        if estimated <= max_tokens:
            return [prompt]

        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', prompt)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.estimate_token_count(sentence)

            if current_tokens + sentence_tokens > max_tokens:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [sentence]
                    current_tokens = sentence_tokens
                else:
                    # Single sentence too long, truncate it
                    chunks.append(self.truncate_prompt(sentence, max_tokens))
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def clean_prompt(self, prompt: str) -> str:
        """
        Clean and normalize prompt

        Args:
            prompt: Input prompt

        Returns:
            Cleaned prompt
        """
        # Remove extra whitespace
        cleaned = ' '.join(prompt.split())

        # Remove redundant commas
        cleaned = re.sub(r',\s*,', ',', cleaned)

        # Ensure comma spacing
        cleaned = re.sub(r',(?!\s)', ', ', cleaned)

        # Remove trailing comma
        cleaned = cleaned.rstrip(',').strip()

        return cleaned

    def extract_keywords(self, prompt: str) -> List[str]:
        """
        Extract main keywords from prompt

        Args:
            prompt: Input prompt

        Returns:
            List of keywords
        """
        # Split by comma and extract main terms
        parts = [p.strip() for p in prompt.split(',')]

        # Remove common filler words
        filler = {'a', 'an', 'the', 'with', 'and', 'or', 'in', 'on', 'at'}

        keywords = []
        for part in parts:
            words = part.split()
            # Keep only meaningful words
            keywords.extend([w for w in words if w.lower() not in filler and len(w) > 2])

        return keywords[:10]  # Return top 10 keywords


def validate_and_prepare_prompts(
    prompt: str,
    negative_prompt: str = None,
    pipeline: str = "svd"
) -> Tuple[bool, str, str, Optional[str]]:
    """
    Validate and prepare prompts for generation

    Args:
        prompt: Main prompt
        negative_prompt: Negative prompt (optional)
        pipeline: Pipeline type

    Returns:
        Tuple of (is_valid, processed_prompt, processed_negative_prompt, error_message)
    """
    validator = PromptValidator()

    # Validate main prompt
    is_valid, error = validator.validate_prompt(prompt)
    if not is_valid:
        return False, "", "", error

    # Clean and process
    processed_prompt = validator.clean_prompt(prompt)

    # Handle negative prompt
    if negative_prompt and negative_prompt.strip():
        # Validate negative prompt
        is_valid_neg, error_neg = validator.validate_prompt(negative_prompt)
        if not is_valid_neg:
            # Non-critical error, use default
            processed_negative = validator.get_default_negative_prompt(pipeline)
        else:
            processed_negative = validator.clean_prompt(negative_prompt)
    else:
        # Use default negative prompt
        processed_negative = validator.get_default_negative_prompt(pipeline)

    return True, processed_prompt, processed_negative, None


# Example usage and testing
if __name__ == "__main__":
    print("Prompt Utilities Test\n")

    validator = PromptValidator()

    # Test prompts
    test_prompts = [
        "",  # Empty (should fail)
        "ab",  # Too short (should fail)
        "slow cinematic zoom in, dramatic lighting",  # Valid
        "a " * 100,  # Too long (should fail)
        "cinematic dolly shot forward, person walking, wind blowing through hair, golden hour lighting, dreamy atmosphere, film grain, masterpiece, best quality, highly detailed, 8k, ultra realistic",  # Long but valid
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"Test {i}: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")

        is_valid, error = validator.validate_prompt(prompt)

        if is_valid:
            tokens = validator.estimate_token_count(prompt)
            print(f"  ✅ Valid ({tokens} tokens)")

            if tokens > 77:
                truncated = validator.truncate_prompt(prompt)
                print(f"  Truncated: {truncated}")

            keywords = validator.extract_keywords(prompt)
            print(f"  Keywords: {', '.join(keywords[:5])}")
        else:
            print(f"  ❌ Invalid: {error}")

        print()

    # Test enhancement
    print("=" * 50 + "\n")
    print("Prompt Enhancement Test:")

    simple_prompt = "person walking, cinematic"
    enhanced = validator.enhance_prompt(simple_prompt, add_quality_tags=True, pipeline="animatediff")

    print(f"Original: {simple_prompt}")
    print(f"Enhanced: {enhanced}")

    # Test cleaning
    print("\n" + "=" * 50 + "\n")
    print("Prompt Cleaning Test:")

    messy_prompt = "slow   zoom  in  ,, dramatic   lighting  ,,  cinematic,  "
    cleaned = validator.clean_prompt(messy_prompt)

    print(f"Messy:   '{messy_prompt}'")
    print(f"Cleaned: '{cleaned}'")

    # Test validation and preparation
    print("\n" + "=" * 50 + "\n")
    print("Full Validation Test:")

    is_valid, proc_prompt, proc_neg, error = validate_and_prepare_prompts(
        prompt="slow cinematic zoom in, dramatic lighting",
        negative_prompt="blurry, static",
        pipeline="animatediff"
    )

    if is_valid:
        print("✅ Validation passed")
        print(f"Processed prompt: {proc_prompt}")
        print(f"Processed negative: {proc_neg}")
    else:
        print(f"❌ Validation failed: {error}")
