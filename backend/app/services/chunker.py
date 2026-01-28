import tiktoken
from typing import List

class ContentChunker:
    """Service to split large content into manageable chunks for AI analysis"""

    def __init__(self, max_tokens: int = 3000, overlap: int = 200):
        """
        Initialize chunker

        Args:
            max_tokens: Maximum tokens per chunk
            overlap: Number of tokens to overlap between chunks for context
        """
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.encoding = tiktoken.encoding_for_model("gpt-4")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text"""
        return len(self.encoding.encode(text))

    def chunk_content(self, content: str) -> List[str]:
        """
        Split content into chunks based on token limit

        Args:
            content: The full text content to chunk

        Returns:
            List of text chunks
        """
        # If content is small enough, return as single chunk
        total_tokens = self.count_tokens(content)
        if total_tokens <= self.max_tokens:
            return [content]

        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        current_tokens = 0

        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)

            # If single paragraph exceeds max_tokens, split it further
            if paragraph_tokens > self.max_tokens:
                # If we have accumulated content, save it
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0

                # Split long paragraph by sentences
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sentence_tokens = self.count_tokens(sentence)

                    if current_tokens + sentence_tokens > self.max_tokens:
                        if current_chunk:
                            chunks.append(current_chunk.strip())

                        # Start new chunk with overlap from previous
                        if chunks and self.overlap > 0:
                            overlap_text = self._get_overlap_text(chunks[-1])
                            current_chunk = overlap_text + sentence + '. '
                            current_tokens = self.count_tokens(current_chunk)
                        else:
                            current_chunk = sentence + '. '
                            current_tokens = sentence_tokens
                    else:
                        current_chunk += sentence + '. '
                        current_tokens += sentence_tokens
            else:
                # Check if adding this paragraph exceeds limit
                if current_tokens + paragraph_tokens > self.max_tokens:
                    # Save current chunk
                    if current_chunk:
                        chunks.append(current_chunk.strip())

                    # Start new chunk with overlap
                    if chunks and self.overlap > 0:
                        overlap_text = self._get_overlap_text(chunks[-1])
                        current_chunk = overlap_text + paragraph + '\n\n'
                        current_tokens = self.count_tokens(current_chunk)
                    else:
                        current_chunk = paragraph + '\n\n'
                        current_tokens = paragraph_tokens
                else:
                    current_chunk += paragraph + '\n\n'
                    current_tokens += paragraph_tokens

        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _get_overlap_text(self, previous_chunk: str) -> str:
        """Get the last portion of a chunk for overlap"""
        tokens = self.encoding.encode(previous_chunk)
        if len(tokens) <= self.overlap:
            return previous_chunk + '\n\n'

        overlap_tokens = tokens[-self.overlap:]
        overlap_text = self.encoding.decode(overlap_tokens)
        return overlap_text + '\n\n'
