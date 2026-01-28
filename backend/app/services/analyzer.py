from openai import OpenAI
from typing import List, Dict, Any
import json
import os

class ContentAnalyzer:
    """Service to analyze website content using OpenAI GPT-4"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def analyze_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> Dict[str, Any]:
        """
        Analyze a single chunk of content

        Args:
            chunk: Text content to analyze
            chunk_index: Index of this chunk (0-based)
            total_chunks: Total number of chunks

        Returns:
            Dictionary with analysis results
        """
        prompt = self._build_analysis_prompt(chunk, chunk_index, total_chunks)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content analyst specializing in detecting misinformation, propaganda, and evaluating source credibility. Provide objective, evidence-based analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")

    def aggregate_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate analysis results from multiple chunks into final analysis

        Args:
            chunk_results: List of analysis results from each chunk

        Returns:
            Aggregated final analysis
        """
        if not chunk_results:
            raise ValueError("No chunk results to aggregate")

        # If only one chunk, return its result directly
        if len(chunk_results) == 1:
            return chunk_results[0]

        # Aggregate multiple chunks
        prompt = self._build_aggregation_prompt(chunk_results)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are synthesizing multiple analyses of chunks from the same website. Provide a coherent, unified analysis that considers all chunks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            raise Exception(f"Result aggregation failed: {str(e)}")

    def _build_analysis_prompt(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """Build the prompt for analyzing a single chunk"""
        chunk_info = f"(Chunk {chunk_index + 1} of {total_chunks})" if total_chunks > 1 else ""

        return f"""Analyze the following website content {chunk_info} and provide a detailed assessment:

CONTENT:
{chunk}

Please analyze this content and respond with a JSON object containing:

1. "out_of_context": Determine if the content contains out-of-context information, misleading framing, or cherry-picked facts. Return "Yes", "No", or "Uncertain" with explanation.

2. "propaganda": Assess if the content uses propaganda techniques such as:
   - Emotional manipulation
   - One-sided presentation
   - Demonization or scapegoating
   - Loaded language
   - False dichotomies
   Return "Yes", "No", or "Uncertain" with explanation.

3. "credibility_score": Rate the content's credibility on a scale of 0-100, considering:
   - Source citations and references
   - Factual accuracy (if verifiable)
   - Balanced presentation
   - Transparency about methodology or sources
   - Professional tone vs sensationalism

4. "content_context": Provide a brief (2-3 sentences) description of what this content is about and its overall nature (news, opinion, educational, commercial, etc.).

5. "key_concerns": List any specific red flags or concerning elements (max 3-5 bullet points).

6. "positive_indicators": List any positive credibility indicators (max 3-5 bullet points).

Return ONLY valid JSON in this exact format:
{{
    "out_of_context": {{"assessment": "Yes/No/Uncertain", "explanation": "..."}},
    "propaganda": {{"assessment": "Yes/No/Uncertain", "explanation": "..."}},
    "credibility_score": 75,
    "content_context": "Brief description...",
    "key_concerns": ["concern 1", "concern 2"],
    "positive_indicators": ["indicator 1", "indicator 2"]
}}"""

    def _build_aggregation_prompt(self, chunk_results: List[Dict[str, Any]]) -> str:
        """Build prompt for aggregating multiple chunk analyses"""
        chunks_summary = json.dumps(chunk_results, indent=2)

        return f"""You have analyzed multiple chunks from the same website. Here are the individual analyses:

{chunks_summary}

Please provide a unified, coherent analysis that synthesizes these chunk-level analyses. Consider:
- Consistent patterns across chunks
- Any contradictions or variations
- Overall impression of the entire content
- Weighted credibility based on all chunks

Return ONLY valid JSON in this exact format:
{{
    "out_of_context": {{"assessment": "Yes/No/Uncertain", "explanation": "..."}},
    "propaganda": {{"assessment": "Yes/No/Uncertain", "explanation": "..."}},
    "credibility_score": 75,
    "content_context": "Brief description...",
    "key_concerns": ["concern 1", "concern 2"],
    "positive_indicators": ["indicator 1", "indicator 2"],
    "summary": "Overall assessment considering all chunks..."
}}"""
