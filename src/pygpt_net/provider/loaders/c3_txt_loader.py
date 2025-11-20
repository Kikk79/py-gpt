#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package              #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2025.11.20                           #
# ================================================== #

"""
C3 Unified Document Loader for plain text files (.txt, .log).

This module implements the C3 UnifiedDocumentLoader interface for plain text files,
providing streaming capabilities, progress tracking, and standardized error handling.
"""

from pathlib import Path
from typing import List, Optional, BinaryIO, Union
import os

from pygpt_net.core.document_processor import (
    UnifiedDocumentLoader,
    DocumentType,
    DocumentMetadata,
    LoadError,
    ErrorSeverity
)


class TxtLoader(UnifiedDocumentLoader):
    """
    Loader for plain text files (.txt, .log).

    Features:
    - UTF-8 and fallback encoding support
    - Chunk-based streaming
    - Automatic encoding detection
    - Proper MIME type detection

    Example:
        >>> loader = TxtLoader(chunk_size=8192)
        >>> for chunk in loader.load_stream("document.txt"):
        ...     process(chunk)
    """

    def __init__(
        self,
        chunk_size: int = UnifiedDocumentLoader.DEFAULT_CHUNK_SIZE,
        encoding: str = "utf-8",
        fallback_encodings: Optional[List[str]] = None
    ):
        """
        Initialize TXT loader.

        Args:
            chunk_size: Size of chunks for streaming (in bytes)
            encoding: Primary encoding to try
            fallback_encodings: List of fallback encodings to try
        """
        super().__init__(chunk_size=chunk_size)
        self.encoding = encoding
        self.fallback_encodings = fallback_encodings or ["latin-1", "cp1252"]
        self._file_handle: Optional[BinaryIO] = None

    def get_supported_types(self) -> List[DocumentType]:
        """
        Return list of document types supported by this loader.

        Returns:
            List containing DocumentType.TXT
        """
        return [DocumentType.TXT]

    def can_handle(self, source: str) -> bool:
        """
        Check if this loader can handle the given source.

        Args:
            source: Path to file

        Returns:
            True if source is a .txt or .log file
        """
        path = Path(source)
        return (
            path.exists() and
            path.is_file() and
            path.suffix.lower() in [".txt", ".log", ".text"]
        )

    def _open_source(self, source: str) -> BinaryIO:
        """
        Open text file in binary mode for reading.

        Args:
            source: Path to file

        Returns:
            Binary file handle

        Raises:
            LoadError: If file cannot be opened
        """
        try:
            self._file_handle = open(source, "rb")
            return self._file_handle
        except FileNotFoundError as e:
            raise LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"File not found: {source}",
                error_code="FILE_NOT_FOUND",
                source=source,
                exception=e
            )
        except PermissionError as e:
            raise LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"Permission denied: {source}",
                error_code="PERMISSION_DENIED",
                source=source,
                exception=e
            )
        except Exception as e:
            raise LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"Failed to open file: {str(e)}",
                error_code="FILE_OPEN_FAILED",
                source=source,
                exception=e
            )

    def _read_chunk(self, file_obj: Union[BinaryIO, Path]) -> Optional[bytes]:
        """
        Read next chunk from the opened file.

        Args:
            file_obj: Binary file handle

        Returns:
            Chunk of bytes, or None if EOF

        Raises:
            LoadError: If read fails
        """
        try:
            chunk = file_obj.read(self.chunk_size)
            return chunk if chunk else None
        except Exception as e:
            source = str(file_obj.name) if hasattr(file_obj, "name") else str(file_obj)
            raise LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"Failed to read chunk: {str(e)}",
                error_code="READ_FAILED",
                source=source,
                exception=e
            )

    def _process_chunk(self, chunk: bytes) -> str:
        """
        Process raw chunk into text using encoding detection.

        This method handles decoding with multiple encoding fallbacks.

        Args:
            chunk: Raw bytes from file

        Returns:
            Decoded text string

        Raises:
            LoadError: If processing fails (shouldn't happen due to fallbacks)
        """
        # Try primary encoding
        try:
            return chunk.decode(self.encoding)
        except UnicodeDecodeError:
            pass

        # Try fallback encodings
        for fallback in self.fallback_encodings:
            try:
                self._add_warning(
                    f"Falling back to {fallback} encoding",
                    "ENCODING_FALLBACK",
                    "text_decoder"
                )
                return chunk.decode(fallback)
            except UnicodeDecodeError:
                continue

        # Last resort: decode with errors='replace' to prevent data loss
        self._add_warning(
            "Using lossy decoding (replacing invalid characters)",
            "LOSSY_DECODING",
            "text_decoder"
        )
        return chunk.decode(self.encoding, errors="replace")

    def _extract_metadata(self, source: str) -> DocumentMetadata:
        """
        Extract metadata from text file.

        Args:
            source: Path to file

        Returns:
            DocumentMetadata with file information
        """
        path = Path(source)
        stat = path.stat()

        # Detect MIME type
        ext = path.suffix.lower()
        if ext == ".txt":
            mime_type = "text/plain"
        elif ext == ".log":
            mime_type = "text/plain"
        else:
            mime_type = "text/plain"

        # Try to detect line count without loading entire file
        line_count = 0
        try:
            with open(source, 'rb') as f:
                # Count newlines efficiently
                for _ in f:
                    line_count += 1
        except Exception:
            line_count = None

        return DocumentMetadata(
            source=source,
            document_type=DocumentType.TXT,
            size_bytes=stat.st_size,
            created_at=None,  # Use datetime if available
            modified_at=None,
            encoding=self.encoding,
            mime_type=mime_type,
            title=path.name,
            custom_metadata={
                "line_count": line_count,
                "extension": ext
            }
        )
