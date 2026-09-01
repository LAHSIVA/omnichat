class TextChunker:
    def __init__(
        self,
        max_characters=500,
        overlap_characters=50,
    ):
        if max_characters <= 0:
            raise ValueError(
                "max_characters must be greater than zero."
            )

        if overlap_characters < 0:
            raise ValueError(
                "overlap_characters cannot be negative."
            )

        if overlap_characters >= max_characters:
            raise ValueError(
                "overlap_characters must be smaller than "
                "max_characters."
            )

        self.max_characters = max_characters
        self.overlap_characters = overlap_characters

    def chunk(self, text):
        if not text or not text.strip():
            return []

        text = text.strip()

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(
                start + self.max_characters,
                text_length,
            )

            if end < text_length:
                whitespace_position = text.rfind(
                    " ",
                    start,
                    end,
                )

                if whitespace_position > start:
                    end = whitespace_position

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            next_start = end - self.overlap_characters

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks