#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2025.11.20 00:00:00                  #
# ================================================== #

"""
Document Viewers Package
Phase 1 Week 3 - B1 UI Component Engineer

This package provides specialized document viewers for different content types:
- CodeDocumentViewer: Syntax highlighting for code files
- PDFDocumentViewer: PDF rendering with pagination
- ImageDocumentViewer: Image display with zoom/pan
- MediaDocumentViewer: Audio/video playback

All viewers extend the BaseDocumentViewer interface for consistent API usage.
"""

from .base import BaseDocumentViewer
from .code import CodeDocumentViewer
from .pdf import PDFDocumentViewer
from .image import ImageDocumentViewer
from .media import MediaDocumentViewer

__all__ = [
    'BaseDocumentViewer',
    'CodeDocumentViewer',
    'PDFDocumentViewer',
    'ImageDocumentViewer',
    'MediaDocumentViewer',
]
