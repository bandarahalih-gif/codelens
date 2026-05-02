"""MiMo API client — OpenAI-compatible interface for Xiaomi MiMo v2.5."""

import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert code reviewer and security analyst. Analyze the provided code for:

1. **Bugs & Logic Errors**: Off-by-one, null dereference, race conditions, unhandled exceptions
2. **Security Vulnerabilities**: SQL injection, XSS, path traversal, insecure deserialization, hardcoded secrets (OWASP Top 10)
3. **Code Style**: Naming conventions, dead code, complex conditionals, missing docstrings
4. **Performance**: N+1 queries, unnecessary allocations, missing caching opportunities, O(n²) loops

For each finding, return a JSON object with:
- category: "bug" | "security" | "style" | "performance"
- severity: "critical" | "high" | "medium" | "low"
- title: Short descriptive title
- description: Detailed explanation of the issue
- line_start: Approximate line number (or null)
- line_end: Approximate end line (or null)
- suggestion: How to fix the issue
- cwe_id: CWE identifier for security issues (e.g., "CWE-89") or null

Return a JSON array of findings. If no issues found, return an empty array [].
Be thorough but avoid false positives. Focus on real, actionable issues."""


class MiMoClient:
    """Client for Xiaomi MiMo API (OpenAI-compatible)."""

    def __init__(self, api_key: str, base_url: str, model: str = "MiMo-v2.5"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def analyze_code(self, source_code: str, language: str, filename: str) -> dict:
        """Analyze source code and return findings + token usage."""
        user_msg = f"""Analyze this {language} file: `{filename}`

```{language}
{source_code}
```

Return findings as a JSON array."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=4096,
            )

            content = response.choices[0].message.content or "[]"
            usage = response.usage

            # Parse findings
            import json
            # Extract JSON from response (may be wrapped in markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            findings = json.loads(content.strip())
            if not isinstance(findings, list):
                findings = []

            return {
                "findings": findings,
                "tokens_used": (usage.prompt_tokens or 0) + (usage.completion_tokens or 0),
                "prompt_tokens": usage.prompt_tokens or 0,
                "completion_tokens": usage.completion_tokens or 0,
            }
        except json.JSONDecodeError:
            logger.warning("Failed to parse MiMo response as JSON for %s", filename)
            return {"findings": [], "tokens_used": 0, "prompt_tokens": 0, "completion_tokens": 0}
        except Exception as e:
            logger.error("MiMo API error for %s: %s", filename, e)
            raise
