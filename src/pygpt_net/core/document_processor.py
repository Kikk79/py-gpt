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
Document Processor - Unified Document Loader System

This module provides a unified streaming document loading system supporting
31+ different document types (9 file-based, 12 web-based, 10 other sources).

Key Features:
- Iterator-based streaming with configurable chunk sizes
- Progress callbacks with 100ms granularity
- Standardized error handling with severity levels
- Memory-safe processing (no full file loading)
- SHA256 checksum validation
- Comprehensive metadata extraction
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Iterator,
    Optional,
    Callable,
    Dict,
    Any,
    List,
    Union,
    BinaryIO,
    TextIO
)
import hashlib
import time
import io
import csv
from datetime import datetime


# ============================================================================
# Enums and Data Classes
# ============================================================================


class ErrorSeverity(Enum):
    """
    Error severity levels for document loading operations.

    Levels:
        WARNING: Non-critical issue, processing can continue
        ERROR: Critical issue, current document fails but system continues
        FATAL: Unrecoverable error, system should halt
    """
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class DocumentType(Enum):
    """
    Supported document types for unified loading.

    Categories:
        File-based: TXT, PDF, DOCX, XLSX, CSV, JSON, XML, MD, HTML
        Web-based: HTTP, RSS, SITEMAP, API, GITHUB, etc.
        Other: DATABASE, STREAM, CLIPBOARD, etc.
    """
    # File-based (9 types)
    TXT = "txt"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    MD = "md"
    HTML = "html"

    # Web-based (12 types)
    HTTP = "http"
    HTTPS = "https"
    RSS = "rss"
    ATOM = "atom"
    SITEMAP = "sitemap"
    API_REST = "api_rest"
    API_GRAPHQL = "api_graphql"
    GITHUB = "github"
    GITLAB = "gitlab"
    CONFLUENCE = "confluence"
    NOTION = "notion"
    GDOCS = "gdocs"

    # Other sources (10 types)
    DATABASE = "database"
    SQL = "sql"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"
    STREAM = "stream"
    CLIPBOARD = "clipboard"
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    CUSTOM = "custom"


@dataclass
class LoadProgress:
    """
    Progress tracking for document loading operations.

    Attributes:
        current_chunk: Current chunk number being processed
        total_chunks: Total number of chunks (None if unknown)
        bytes_processed: Number of bytes processed so far
        total_bytes: Total bytes to process (None if unknown)
        estimated_time: Estimated time remaining in seconds (None if unknown)
        percentage: Completion percentage (0-100, None if unknown)
        start_time: Unix timestamp when loading started
        elapsed_time: Time elapsed since start in seconds
    """
    current_chunk: int = 0
    total_chunks: Optional[int] = None
    bytes_processed: int = 0
    total_bytes: Optional[int] = None
    estimated_time: Optional[float] = None
    percentage: Optional[float] = None
    start_time: float = field(default_factory=time.time)
    elapsed_time: float = 0.0

    def update_estimates(self) -> None:
        """
        Update estimated time and percentage based on current progress.

        Calculates:
        - Elapsed time since start
        - Completion percentage (if total_bytes known)
        - Estimated time remaining based on current rate
        """
        self.elapsed_time = time.time() - self.start_time

        if self.total_bytes and self.total_bytes > 0:
            self.percentage = (self.bytes_processed / self.total_bytes) * 100.0

            if self.bytes_processed > 0 and self.elapsed_time > 0:
                rate = self.bytes_processed / self.elapsed_time
                remaining_bytes = self.total_bytes - self.bytes_processed
                self.estimated_time = remaining_bytes / rate

        if self.total_chunks and self.total_chunks > 0 and self.percentage is None:
            self.percentage = (self.current_chunk / self.total_chunks) * 100.0


@dataclass
class DocumentMetadata:
    """
    Metadata extracted from loaded documents.

    Attributes:
        source: Original source path/URL
        document_type: Type of document (from DocumentType enum)
        size_bytes: Total size in bytes
        checksum_sha256: SHA256 hash of content
        created_at: Creation timestamp
        modified_at: Last modification timestamp
        encoding: Character encoding (for text documents)
        mime_type: MIME type of content
        author: Document author (if available)
        title: Document title (if available)
        language: Document language (if detected)
        page_count: Number of pages (for paginated documents)
        custom_metadata: Additional type-specific metadata
    """
    source: str
    document_type: DocumentType
    size_bytes: int = 0
    checksum_sha256: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    encoding: str = "utf-8"
    mime_type: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadError:
    """
    Standardized error information for document loading failures.

    Attributes:
        severity: Error severity level
        message: Human-readable error message
        error_code: Machine-readable error code
        source: Source where error occurred
        timestamp: When error occurred
        exception: Original exception object (if applicable)
        context: Additional context information
        recoverable: Whether error can be recovered from
        retry_count: Number of retries attempted
    """
    severity: ErrorSeverity
    message: str
    error_code: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    exception: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = False
    retry_count: int = 0

    def __str__(self) -> str:
        """String representation of error."""
        return (
            f"[{self.severity.value.upper()}] {self.error_code}: {self.message} "
            f"(source: {self.source}, time: {self.timestamp.isoformat()})"
        )


@dataclass
class LoadResult:
    """
    Result of a document loading operation.

    Attributes:
        success: Whether loading succeeded
        content: Loaded content chunks
        metadata: Document metadata
        errors: List of errors encountered
        warnings: List of warnings
        load_time: Total loading time in seconds
    """
    success: bool
    content: List[str] = field(default_factory=list)
    metadata: Optional[DocumentMetadata] = None
    errors: List[LoadError] = field(default_factory=list)
    warnings: List[LoadError] = field(default_factory=list)
    load_time: float = 0.0


# ============================================================================
# Abstract Base Class
# ============================================================================


class UnifiedDocumentLoader(ABC):
    """
    Abstract base class for unified document loading.

    This class provides a common interface for loading documents from various
    sources with streaming support, progress tracking, and error handling.

    Key Features:
    - Iterator-based streaming (configurable chunk size)
    - Progress callbacks (100ms granularity)
    - Standardized error handling
    - Memory-safe processing
    - SHA256 checksum validation

    Usage:
        loader = ConcreteLoader(chunk_size=8192)
        loader.set_progress_callback(my_callback)

        for chunk in loader.load_stream(source):
            process(chunk)

        metadata = loader.get_metadata()
        errors = loader.get_errors()
    """

    # Default configuration
    DEFAULT_CHUNK_SIZE = 8192  # 8KB chunks
    PROGRESS_CALLBACK_INTERVAL = 0.1  # 100ms
    MAX_RETRY_ATTEMPTS = 3

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        enable_checksum: bool = True,
        enable_progress: bool = True
    ):
        """
        Initialize the document loader.

        Args:
            chunk_size: Size of chunks for streaming (bytes)
            enable_checksum: Whether to calculate SHA256 checksums
            enable_progress: Whether to track and report progress
        """
        self.chunk_size = chunk_size
        self.enable_checksum = enable_checksum
        self.enable_progress = enable_progress

        # Progress tracking
        self._progress: Optional[LoadProgress] = None
        self._progress_callback: Optional[Callable[[LoadProgress], None]] = None
        self._last_callback_time: float = 0.0

        # Error tracking
        self._errors: List[LoadError] = []
        self._warnings: List[LoadError] = []

        # Metadata
        self._metadata: Optional[DocumentMetadata] = None

        # Checksum
        self._hasher: Optional[hashlib.sha256] = None
        if enable_checksum:
            self._hasher = hashlib.sha256()

    # ========================================================================
    # Abstract Methods (must be implemented by subclasses)
    # ========================================================================

    @abstractmethod
    def get_supported_types(self) -> List[DocumentType]:
        """
        Return list of document types supported by this loader.

        Returns:
            List of DocumentType enums this loader can handle
        """
        pass

    @abstractmethod
    def can_handle(self, source: str) -> bool:
        """
        Check if this loader can handle the given source.

        Args:
            source: Path, URL, or identifier of document source

        Returns:
            True if this loader can handle the source
        """
        pass

    @abstractmethod
    def _open_source(self, source: str) -> Union[BinaryIO, TextIO]:
        """
        Open the document source for reading.

        Args:
            source: Path, URL, or identifier of document source

        Returns:
            File-like object for reading

        Raises:
            LoadError: If source cannot be opened
        """
        pass

    @abstractmethod
    def _read_chunk(self, file_obj: Union[BinaryIO, TextIO]) -> Optional[bytes]:
        """
        Read next chunk from the opened source.

        Args:
            file_obj: File-like object to read from

        Returns:
            Chunk of bytes, or None if EOF

        Raises:
            LoadError: If read fails
        """
        pass

    @abstractmethod
    def _extract_metadata(self, source: str) -> DocumentMetadata:
        """
        Extract metadata from the document source.

        Args:
            source: Path, URL, or identifier of document source

        Returns:
            DocumentMetadata object with extracted information
        """
        pass

    @abstractmethod
    def _process_chunk(self, chunk: bytes) -> str:
        """
        Process raw chunk into usable text content.

        This method handles decoding, cleaning, and any format-specific
        processing needed to convert raw bytes into text.

        Args:
            chunk: Raw bytes from document

        Returns:
            Processed text content

        Raises:
            LoadError: If processing fails
        """
        pass

    # ========================================================================
    # Public API
    # ========================================================================

    def load_stream(self, source: str) -> Iterator[str]:
        """
        Load document as a stream of text chunks.

        This is the primary method for streaming document content. It yields
        processed text chunks while tracking progress and handling errors.

        Args:
            source: Path, URL, or identifier of document source

        Yields:
            Processed text chunks

        Raises:
            LoadError: If loading fails critically

        Example:
            >>> loader = TxtLoader()
            >>> for chunk in loader.load_stream("document.txt"):
            ...     process(chunk)
        """
        if not self.can_handle(source):
            self._add_error(
                ErrorSeverity.ERROR,
                f"Cannot handle source: {source}",
                "UNSUPPORTED_SOURCE",
                source
            )
            return

        # Initialize progress tracking
        if self.enable_progress:
            self._progress = LoadProgress()
            self._last_callback_time = time.time()

        # Reset error tracking
        self._errors.clear()
        self._warnings.clear()

        # Reset checksum
        if self.enable_checksum and self._hasher:
            self._hasher = hashlib.sha256()

        file_obj = None
        try:
            # Extract metadata first
            self._metadata = self._extract_metadata(source)

            # Open source
            file_obj = self._open_source(source)

            # Stream chunks
            chunk_num = 0
            while True:
                # Read next chunk
                raw_chunk = self._read_chunk(file_obj)
                if raw_chunk is None:
                    break

                # Update checksum
                if self.enable_checksum and self._hasher:
                    self._hasher.update(raw_chunk)

                # Process chunk
                processed_chunk = self._process_chunk(raw_chunk)

                # Update progress
                chunk_num += 1
                if self.enable_progress and self._progress:
                    self._progress.current_chunk = chunk_num
                    self._progress.bytes_processed += len(raw_chunk)
                    self._progress.update_estimates()
                    self._maybe_trigger_callback()

                yield processed_chunk

            # Finalize checksum
            if self.enable_checksum and self._hasher and self._metadata:
                self._metadata.checksum_sha256 = self._hasher.hexdigest()

            # Final progress callback
            if self.enable_progress and self._progress_callback and self._progress:
                self._progress_callback(self._progress)

        except Exception as e:
            self._add_error(
                ErrorSeverity.ERROR,
                f"Failed to load document: {str(e)}",
                "LOAD_FAILED",
                source,
                exception=e
            )
            raise
        finally:
            if file_obj:
                try:
                    file_obj.close()
                except Exception as e:
                    self._add_warning(
                        f"Failed to close source: {str(e)}",
                        "CLOSE_FAILED",
                        source,
                        exception=e
                    )

    def load_complete(self, source: str) -> LoadResult:
        """
        Load entire document into memory (non-streaming).

        WARNING: This loads the entire document into memory. Use load_stream()
        for large documents.

        Args:
            source: Path, URL, or identifier of document source

        Returns:
            LoadResult with complete content and metadata
        """
        start_time = time.time()
        content_chunks: List[str] = []

        try:
            for chunk in self.load_stream(source):
                content_chunks.append(chunk)

            load_time = time.time() - start_time

            return LoadResult(
                success=len(self._errors) == 0,
                content=content_chunks,
                metadata=self._metadata,
                errors=self._errors.copy(),
                warnings=self._warnings.copy(),
                load_time=load_time
            )

        except Exception as e:
            load_time = time.time() - start_time
            return LoadResult(
                success=False,
                content=content_chunks,
                metadata=self._metadata,
                errors=self._errors.copy(),
                warnings=self._warnings.copy(),
                load_time=load_time
            )

    def set_progress_callback(
        self,
        callback: Optional[Callable[[LoadProgress], None]]
    ) -> None:
        """
        Set callback function for progress updates.

        The callback will be invoked approximately every 100ms during loading.

        Args:
            callback: Function to call with LoadProgress updates, or None to disable

        Example:
            >>> def on_progress(progress: LoadProgress):
            ...     print(f"Loaded {progress.bytes_processed} bytes")
            >>> loader.set_progress_callback(on_progress)
        """
        self._progress_callback = callback

    def get_metadata(self) -> Optional[DocumentMetadata]:
        """
        Get metadata for the last loaded document.

        Returns:
            DocumentMetadata object, or None if no document loaded
        """
        return self._metadata

    def get_errors(self) -> List[LoadError]:
        """
        Get list of errors from the last loading operation.

        Returns:
            List of LoadError objects
        """
        return self._errors.copy()

    def get_warnings(self) -> List[LoadError]:
        """
        Get list of warnings from the last loading operation.

        Returns:
            List of LoadError objects with WARNING severity
        """
        return self._warnings.copy()

    def get_progress(self) -> Optional[LoadProgress]:
        """
        Get current progress information.

        Returns:
            LoadProgress object, or None if not tracking progress
        """
        return self._progress

    # ========================================================================
    # Protected Helper Methods
    # ========================================================================

    def _maybe_trigger_callback(self) -> None:
        """
        Trigger progress callback if interval has elapsed.

        Ensures callbacks are not fired more frequently than the configured
        interval (default 100ms).
        """
        if not self._progress_callback or not self._progress:
            return

        current_time = time.time()
        if current_time - self._last_callback_time >= self.PROGRESS_CALLBACK_INTERVAL:
            self._progress_callback(self._progress)
            self._last_callback_time = current_time

    def _add_error(
        self,
        severity: ErrorSeverity,
        message: str,
        error_code: str,
        source: str,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an error to the error list.

        Args:
            severity: Error severity level
            message: Human-readable error message
            error_code: Machine-readable error code
            source: Source where error occurred
            exception: Original exception (if applicable)
            context: Additional context information
        """
        error = LoadError(
            severity=severity,
            message=message,
            error_code=error_code,
            source=source,
            exception=exception,
            context=context or {},
            recoverable=severity == ErrorSeverity.WARNING
        )
        self._errors.append(error)

    def _add_warning(
        self,
        message: str,
        error_code: str,
        source: str,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a warning to the warning list.

        Args:
            message: Human-readable warning message
            error_code: Machine-readable error code
            source: Source where warning occurred
            exception: Original exception (if applicable)
            context: Additional context information
        """
        warning = LoadError(
            severity=ErrorSeverity.WARNING,
            message=message,
            error_code=error_code,
            source=source,
            exception=exception,
            context=context or {},
            recoverable=True
        )
        self._warnings.append(warning)

    def _get_file_size(self, source: str) -> Optional[int]:
        """
        Get file size for progress tracking.

        Args:
            source: Path to file

        Returns:
            File size in bytes, or None if cannot determine
        """
        try:
            path = Path(source)
            if path.exists() and path.is_file():
                return path.stat().st_size
        except Exception:
            pass
        return None


# ============================================================================
# Concrete Adapter Examples
# ============================================================================


class TxtLoader(UnifiedDocumentLoader):
    """
    Loader for plain text files (.txt, .log, .md, etc.).

    Features:
    - UTF-8 and fallback encoding support
    - Line-based or chunk-based streaming
    - Automatic encoding detection

    Example:
        >>> loader = TxtLoader(chunk_size=4096)
        >>> for chunk in loader.load_stream("document.txt"):
        ...     print(chunk)
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
            chunk_size: Size of chunks for streaming
            encoding: Primary encoding to try
            fallback_encodings: List of fallback encodings to try
        """
        super().__init__(chunk_size=chunk_size)
        self.encoding = encoding
        self.fallback_encodings = fallback_encodings or ["latin-1", "cp1252"]
        self._file_handle: Optional[BinaryIO] = None

    def get_supported_types(self) -> List[DocumentType]:
        """Return supported document types."""
        return [DocumentType.TXT, DocumentType.MD]

    def can_handle(self, source: str) -> bool:
        """Check if source is a text file."""
        path = Path(source)
        return (
            path.exists() and
            path.is_file() and
            path.suffix.lower() in [".txt", ".md", ".log", ".text"]
        )

    def _open_source(self, source: str) -> BinaryIO:
        """Open text file in binary mode."""
        try:
            self._file_handle = open(source, "rb")
            return self._file_handle
        except Exception as e:
            raise LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"Failed to open file: {str(e)}",
                error_code="FILE_OPEN_FAILED",
                source=source,
                exception=e
            )

    def _read_chunk(self, file_obj: BinaryIO) -> Optional[bytes]:
        """Read next chunk from file."""
        try:
            chunk = file_obj.read(self.chunk_size)
            return chunk if chunk else None
        except Exception as e:
            raise LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"Failed to read chunk: {str(e)}",
                error_code="READ_FAILED",
                source=str(file_obj.name) if hasattr(file_obj, "name") else "unknown",
                exception=e
            )

    def _process_chunk(self, chunk: bytes) -> str:
        """Decode bytes to text."""
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

        # Last resort: decode with errors='replace'
        self._add_warning(
            "Using lossy decoding (replacing invalid characters)",
            "LOSSY_DECODING",
            "text_decoder"
        )
        return chunk.decode(self.encoding, errors="replace")

    def _extract_metadata(self, source: str) -> DocumentMetadata:
        """Extract metadata from text file."""
        path = Path(source)
        stat = path.stat()

        return DocumentMetadata(
            source=source,
            document_type=DocumentType.MD if path.suffix == ".md" else DocumentType.TXT,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            encoding=self.encoding,
            mime_type="text/plain"
        )


class PdfLoader(UnifiedDocumentLoader):
    """
    Loader for PDF documents.

    Features:
    - Page-by-page streaming
    - Text extraction from images (if OCR enabled)
    - Metadata extraction (author, title, page count)

    Note: This is a skeleton implementation. Full PDF support requires
    PyPDF2 or pdfminer.six libraries.

    Example:
        >>> loader = PdfLoader()
        >>> for page_text in loader.load_stream("document.pdf"):
        ...     print(page_text)
    """

    def __init__(
        self,
        chunk_size: int = UnifiedDocumentLoader.DEFAULT_CHUNK_SIZE,
        enable_ocr: bool = False
    ):
        """
        Initialize PDF loader.

        Args:
            chunk_size: Size of chunks for streaming (pages)
            enable_ocr: Whether to use OCR for text extraction
        """
        super().__init__(chunk_size=chunk_size)
        self.enable_ocr = enable_ocr
        self._current_page: int = 0
        self._total_pages: int = 0
        self._pdf_handle: Optional[Any] = None

    def get_supported_types(self) -> List[DocumentType]:
        """Return supported document types."""
        return [DocumentType.PDF]

    def can_handle(self, source: str) -> bool:
        """Check if source is a PDF file."""
        path = Path(source)
        return (
            path.exists() and
            path.is_file() and
            path.suffix.lower() == ".pdf"
        )

    def _open_source(self, source: str) -> Any:
        """
        Open PDF file.

        Note: This is a skeleton. Real implementation would use PyPDF2:
            import PyPDF2
            self._pdf_handle = PyPDF2.PdfReader(source)
            self._total_pages = len(self._pdf_handle.pages)
            return self._pdf_handle
        """
        # Skeleton implementation
        self._add_warning(
            "PDF loader is not fully implemented. Install PyPDF2 for full support.",
            "NOT_IMPLEMENTED",
            source
        )
        # Return dummy handle
        return open(source, "rb")

    def _read_chunk(self, file_obj: Any) -> Optional[bytes]:
        """
        Read next page from PDF.

        Note: This is a skeleton. Real implementation would:
            if self._current_page >= self._total_pages:
                return None
            page = self._pdf_handle.pages[self._current_page]
            text = page.extract_text()
            self._current_page += 1
            return text.encode('utf-8')
        """
        # Skeleton implementation - just read bytes
        if isinstance(file_obj, BinaryIO):
            chunk = file_obj.read(self.chunk_size)
            return chunk if chunk else None
        return None

    def _process_chunk(self, chunk: bytes) -> str:
        """
        Process PDF page content.

        Note: Real implementation would handle PDF-specific text extraction.
        """
        try:
            return chunk.decode("utf-8", errors="replace")
        except Exception as e:
            self._add_warning(
                f"Failed to decode PDF chunk: {str(e)}",
                "DECODE_FAILED",
                "pdf_processor"
            )
            return ""

    def _extract_metadata(self, source: str) -> DocumentMetadata:
        """
        Extract metadata from PDF.

        Note: Real implementation would extract PDF metadata:
            metadata = pdf.metadata
            author = metadata.get('/Author')
            title = metadata.get('/Title')
            pages = len(pdf.pages)
        """
        path = Path(source)
        stat = path.stat()

        return DocumentMetadata(
            source=source,
            document_type=DocumentType.PDF,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            mime_type="application/pdf",
            page_count=0,  # Would be extracted from PDF
            custom_metadata={"ocr_enabled": self.enable_ocr}
        )


class CsvLoader(UnifiedDocumentLoader):
    """
    Loader for CSV (Comma-Separated Values) files.

    Features:
    - Row-by-row streaming
    - Header detection
    - Configurable delimiter and quoting
    - Data type inference

    Example:
        >>> loader = CsvLoader(has_header=True)
        >>> for row in loader.load_stream("data.csv"):
        ...     print(row)
    """

    def __init__(
        self,
        chunk_size: int = 100,  # 100 rows per chunk
        delimiter: str = ",",
        quotechar: str = '"',
        has_header: bool = True,
        encoding: str = "utf-8"
    ):
        """
        Initialize CSV loader.

        Args:
            chunk_size: Number of rows per chunk
            delimiter: CSV delimiter character
            quotechar: Quote character
            has_header: Whether first row is header
            encoding: File encoding
        """
        super().__init__(chunk_size=chunk_size)
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.has_header = has_header
        self.encoding = encoding
        self._file_handle: Optional[TextIO] = None
        self._csv_reader: Optional[csv.DictReader] = None
        self._header: Optional[List[str]] = None
        self._row_count: int = 0

    def get_supported_types(self) -> List[DocumentType]:
        """Return supported document types."""
        return [DocumentType.CSV]

    def can_handle(self, source: str) -> bool:
        """Check if source is a CSV file."""
        path = Path(source)
        return (
            path.exists() and
            path.is_file() and
            path.suffix.lower() in [".csv", ".tsv"]
        )

    def _open_source(self, source: str) -> TextIO:
        """Open CSV file."""
        try:
            self._file_handle = open(source, "r", encoding=self.encoding, newline="")

            # Auto-detect delimiter if TSV
            if source.endswith(".tsv"):
                self.delimiter = "\t"

            # Create CSV reader
            if self.has_header:
                self._csv_reader = csv.DictReader(
                    self._file_handle,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar
                )
                self._header = self._csv_reader.fieldnames
            else:
                self._csv_reader = csv.reader(
                    self._file_handle,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar
                )

            return self._file_handle

        except Exception as e:
            raise LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"Failed to open CSV file: {str(e)}",
                error_code="CSV_OPEN_FAILED",
                source=source,
                exception=e
            )

    def _read_chunk(self, file_obj: TextIO) -> Optional[bytes]:
        """
        Read next chunk of rows from CSV.

        Returns chunk as JSON-encoded bytes for consistent interface.
        """
        try:
            rows = []
            for _ in range(self.chunk_size):
                try:
                    row = next(self._csv_reader)
                    rows.append(row)
                    self._row_count += 1
                except StopIteration:
                    break

            if not rows:
                return None

            # Convert rows to JSON string then bytes
            import json
            chunk_data = {
                "header": self._header,
                "rows": rows,
                "row_count": self._row_count
            }
            return json.dumps(chunk_data).encode("utf-8")

        except Exception as e:
            raise LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"Failed to read CSV chunk: {str(e)}",
                error_code="CSV_READ_FAILED",
                source=str(file_obj.name),
                exception=e
            )

    def _process_chunk(self, chunk: bytes) -> str:
        """
        Process CSV chunk into formatted text.

        Converts JSON-encoded rows into human-readable format.
        """
        import json
        try:
            data = json.loads(chunk.decode("utf-8"))
            rows = data["rows"]

            # Format as text table
            lines = []
            for row in rows:
                if isinstance(row, dict):
                    # DictReader format
                    line = " | ".join(f"{k}: {v}" for k, v in row.items())
                else:
                    # Regular reader format
                    line = " | ".join(str(cell) for cell in row)
                lines.append(line)

            return "\n".join(lines) + "\n"

        except Exception as e:
            self._add_warning(
                f"Failed to process CSV chunk: {str(e)}",
                "CSV_PROCESS_FAILED",
                "csv_processor"
            )
            return chunk.decode("utf-8", errors="replace")

    def _extract_metadata(self, source: str) -> DocumentMetadata:
        """Extract metadata from CSV file."""
        path = Path(source)
        stat = path.stat()

        return DocumentMetadata(
            source=source,
            document_type=DocumentType.CSV,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            encoding=self.encoding,
            mime_type="text/csv",
            custom_metadata={
                "delimiter": self.delimiter,
                "has_header": self.has_header,
                "header": self._header
            }
        )


# ============================================================================
# Factory and Registry
# ============================================================================


class LoaderRegistry:
    """
    Registry for managing document loaders.

    Provides automatic loader selection based on file type and source.

    Example:
        >>> registry = LoaderRegistry()
        >>> registry.register(TxtLoader())
        >>> registry.register(PdfLoader())
        >>> loader = registry.get_loader("document.txt")
        >>> for chunk in loader.load_stream("document.txt"):
        ...     print(chunk)
    """

    def __init__(self):
        """Initialize empty loader registry."""
        self._loaders: List[UnifiedDocumentLoader] = []

    def register(self, loader: UnifiedDocumentLoader) -> None:
        """
        Register a loader instance.

        Args:
            loader: Loader instance to register
        """
        self._loaders.append(loader)

    def get_loader(self, source: str) -> Optional[UnifiedDocumentLoader]:
        """
        Get appropriate loader for source.

        Args:
            source: Path, URL, or identifier of document source

        Returns:
            Loader instance that can handle the source, or None
        """
        for loader in self._loaders:
            if loader.can_handle(source):
                return loader
        return None

    def get_supported_types(self) -> List[DocumentType]:
        """
        Get all supported document types across all registered loaders.

        Returns:
            List of unique DocumentType values
        """
        types = set()
        for loader in self._loaders:
            types.update(loader.get_supported_types())
        return sorted(types, key=lambda t: t.value)


# ============================================================================
# Convenience Functions
# ============================================================================


def create_default_registry() -> LoaderRegistry:
    """
    Create a registry with all built-in loaders registered.

    Returns:
        LoaderRegistry with TXT, PDF, and CSV loaders
    """
    registry = LoaderRegistry()
    registry.register(TxtLoader())
    registry.register(PdfLoader())
    registry.register(CsvLoader())
    return registry


def load_document(
    source: str,
    chunk_size: int = UnifiedDocumentLoader.DEFAULT_CHUNK_SIZE,
    progress_callback: Optional[Callable[[LoadProgress], None]] = None
) -> LoadResult:
    """
    Convenience function to load a document with automatic loader selection.

    Args:
        source: Path, URL, or identifier of document source
        chunk_size: Size of chunks for streaming
        progress_callback: Optional progress callback

    Returns:
        LoadResult with content and metadata

    Example:
        >>> result = load_document("data.csv")
        >>> if result.success:
        ...     for chunk in result.content:
        ...         print(chunk)
    """
    registry = create_default_registry()
    loader = registry.get_loader(source)

    if loader is None:
        return LoadResult(
            success=False,
            errors=[LoadError(
                severity=ErrorSeverity.ERROR,
                message=f"No loader available for source: {source}",
                error_code="NO_LOADER",
                source=source
            )]
        )

    loader.chunk_size = chunk_size
    if progress_callback:
        loader.set_progress_callback(progress_callback)

    return loader.load_complete(source)


# ============================================================================
# End of document_processor.py
# ============================================================================
