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
Media Document Viewer
Phase 1 Week 3 - B1 UI Component Engineer

Plays audio and video files with full media controls.
Integrates with PySide6's multimedia framework for playback.
"""

from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtCore import Qt, QObject, QUrl, QTimer, Signal
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QSizePolicy, QStyle
)

try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    MULTIMEDIA_AVAILABLE = False

from .base import BaseDocumentViewer


class MediaDocumentViewer(BaseDocumentViewer, QObject):
    """
    Media document viewer for audio and video playback

    Features:
    - Audio playback (MP3, WAV, OGG, FLAC, etc.)
    - Video playback (MP4, AVI, MKV, MOV, etc.)
    - Standard media controls (play/pause, stop, seek)
    - Volume control
    - Playback speed control
    - Time display (current/duration)
    - Progress bar for seeking
    """

    duration_changed = Signal(int)  # duration in ms
    position_changed = Signal(int)  # position in ms
    playback_state_changed = Signal(bool)  # is playing

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize media document viewer

        Args:
            parent: Parent widget
        """
        BaseDocumentViewer.__init__(self, parent)
        QObject.__init__(self, parent)

        self._widget = None
        self._media_player = None
        self._audio_output = None
        self._video_widget = None
        self._is_video = False
        self._duration = 0
        self._position = 0
        self._fallback_mode = not MULTIMEDIA_AVAILABLE

        self._setup_ui()
        self._setup_media_player()
        self._apply_styles()

    def _setup_ui(self):
        """Initialize viewer UI components"""
        # Main widget
        self._widget = QWidget(self.parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Media display area
        self._media_frame = QFrame()
        self._media_frame.setObjectName("media_frame")
        self._media_frame.setFrameStyle(QFrame.StyledPanel)

        media_layout = QVBoxLayout()
        media_layout.setContentsMargins(0, 0, 0, 0)

        if not self._fallback_mode:
            # Video widget for video playback
            self._video_widget = QVideoWidget()
            self._video_widget.setObjectName("video_widget")
            self._video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            media_layout.addWidget(self._video_widget)
        else:
            # Fallback: show placeholder
            self._placeholder = QLabel("Media playback not available\nInstall PySide6[extras]")
            self._placeholder.setObjectName("media_placeholder")
            self._placeholder.setAlignment(Qt.AlignCenter)
            media_layout.addWidget(self._placeholder)

        self._media_frame.setLayout(media_layout)

        # Media controls
        controls = self._create_media_controls()

        # Assemble layout
        layout.addWidget(self._media_frame)
        layout.addWidget(controls)

        self._widget.setLayout(layout)

    def _create_media_controls(self) -> QWidget:
        """Create media control toolbar"""
        controls = QWidget()
        controls.setObjectName("media_controls")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Top row: Progress bar and time display
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self._time_current = QLabel("00:00")
        self._time_current.setObjectName("time_label")
        self._time_current.setFixedWidth(50)

        # Progress slider
        self._progress_slider = QSlider(Qt.Horizontal)
        self._progress_slider.setObjectName("progress_slider")
        self._progress_slider.setRange(0, 0)  # Will be updated with duration
        self._progress_slider.sliderMoved.connect(self._on_seek)
        self._progress_slider.sliderPressed.connect(self._on_seek_start)
        self._progress_slider.sliderReleased.connect(self._on_seek_end)

        self._time_total = QLabel("00:00")
        self._time_total.setObjectName("time_label")
        self._time_total.setFixedWidth(50)

        top_row.addWidget(self._time_current)
        top_row.addWidget(self._progress_slider)
        top_row.addWidget(self._time_total)

        # Bottom row: Playback controls
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        # Play/pause button
        self._play_btn = QPushButton()
        self._play_btn.setObjectName("play_button")
        self._play_btn.setIcon(self._widget.style().standardIcon(QStyle.SP_MediaPlay))
        self._play_btn.clicked.connect(self.play_pause)
        self._play_btn.setEnabled(False)

        # Stop button
        self._stop_btn = QPushButton()
        self._stop_btn.setObjectName("stop_button")
        self._stop_btn.setIcon(self._widget.style().standardIcon(QStyle.SP_MediaStop))
        self._stop_btn.clicked.connect(self.stop)
        self._stop_btn.setEnabled(False)

        # Volume control
        bottom_row.addWidget(QLabel("Volume:"))
        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setObjectName("volume_slider")
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(50)
        self._volume_slider.setFixedWidth(100)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)

        # Playback speed
        bottom_row.addSpacing(20)
        bottom_row.addWidget(QLabel("Speed:"))
        self._speed_combo = QSlider(Qt.Horizontal)
        self._speed_combo.setObjectName("speed_slider")
        self._speed_combo.setRange(50, 200)  # 0.5x to 2.0x
        self._speed_combo.setValue(100)  # 1.0x
        self._speed_combo.setFixedWidth(100)
        self._speed_combo.valueChanged.connect(self._on_speed_changed)
        self._speed_label = QLabel("1.0x")
        self._speed_label.setFixedWidth(40)

        bottom_row.addWidget(self._play_btn)
        bottom_row.addWidget(self._stop_btn)
        bottom_row.addStretch()
        bottom_row.addWidget(self._volume_slider)
        bottom_row.addSpacing(20)
        bottom_row.addWidget(self._speed_combo)
        bottom_row.addWidget(self._speed_label)

        # Assemble controls
        layout.addLayout(top_row)
        layout.addLayout(bottom_row)

        controls.setLayout(layout)
        return controls

    def _setup_media_player(self):
        """Initialize media player components"""
        if self._fallback_mode:
            return

        # Create media player
        self._media_player = QMediaPlayer()
        self._audio_output = QAudioOutput()

        # Connect player to audio output
        self._media_player.setAudioOutput(self._audio_output)

        # Connect player to video widget
        if self._video_widget:
            self._media_player.setVideoOutput(self._video_widget)

        # Connect signals
        self._media_player.durationChanged.connect(self._on_duration_changed)
        self._media_player.positionChanged.connect(self._on_position_changed)
        self._media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._media_player.errorChanged.connect(self._on_error_occurred)

        # Set default volume
        if self._audio_output:
            self._audio_output.setVolume(0.5)

    def _on_duration_changed(self, duration: int):
        """Handle duration change"""
        self._duration = duration
        self._progress_slider.setRange(0, duration)
        self._time_total.setText(self._format_time(duration))
        self.duration_changed.emit(duration)

    def _on_position_changed(self, position: int):
        """Handle position change"""
        if not self._progress_slider.isSliderDown():
            self._progress_slider.blockSignals(True)
            self._progress_slider.setValue(position)
            self._progress_slider.blockSignals(False)

        self._position = position
        self._time_current.setText(self._format_time(position))
        self.position_changed.emit(position)

    def _on_playback_state_changed(self, state):
        """Handle playback state change"""
        is_playing = (state == QMediaPlayer.PlayingState)

        # Update play button icon
        if is_playing:
            self._play_btn.setIcon(self._widget.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self._play_btn.setIcon(self._widget.style().standardIcon(QStyle.SP_MediaPlay))

        self.playback_state_changed.emit(is_playing)

    def _on_media_status_changed(self, status):
        """Handle media status change"""
        if status == QMediaPlayer.LoadedMedia:
            self._play_btn.setEnabled(True)
            self._stop_btn.setEnabled(True)
        elif status == QMediaPlayer.EndOfMedia:
            self.stop()

    def _on_error_occurred(self):
        """Handle playback error"""
        if self._media_player and self._media_player.error() != QMediaPlayer.NoError:
            error_msg = self._media_player.errorString()
            self._emit_error(f"Media playback error: {error_msg}")

    def _on_seek(self, position: int):
        """Handle manual seek"""
        self._time_current.setText(self._format_time(position))

    def _on_seek_start(self):
        """Handle seek start"""
        self._media_player.blockSignals(True)

    def _on_seek_end(self):
        """Handle seek end"""
        if self._media_player:
            self._media_player.blockSignals(False)
            self._media_player.setPosition(self._progress_slider.value())

    def _on_volume_changed(self, volume: int):
        """Handle volume change"""
        if self._audio_output:
            self._audio_output.setVolume(volume / 100.0)

    def _on_speed_changed(self, speed: int):
        """Handle playback speed change"""
        if self._media_player:
            speed_val = speed / 100.0
            self._media_player.setPlaybackRate(speed_val)
            self._speed_label.setText(f"{speed_val:.1f}x")

    @staticmethod
    def _format_time(ms: int) -> str:
        """
        Format milliseconds to MM:SS

        Args:
            ms: Time in milliseconds

        Returns:
            Formatted time string
        """
        if ms <= 0:
            return "00:00"

        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes:02d}:{seconds:02d}"

    def _detect_media_type(self, file_path: Path) -> str:
        """
        Detect media type from file extension

        Args:
            file_path: Path to media file

        Returns:
            Media type: 'audio' or 'video'
        """
        video_exts = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg']
        audio_exts = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus', '.mid', '.midi']

        ext = file_path.suffix.lower()
        self._is_video = ext in video_exts

        if ext in video_exts:
            return 'video'
        elif ext in audio_exts:
            return 'audio'
        else:
            # Default to audio if unknown
            return 'audio'

    def load_document(self, file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load media file

        Args:
            file_path: Path to media file
            metadata: Optional metadata

        Returns:
            True if loaded successfully
        """
        try:
            self._emit_loading_started()

            if self._fallback_mode:
                self._emit_loading_progress(100)
                self._emit_error("Media playback not available in fallback mode")
                return False

            self._file_path = file_path

            # Detect media type
            media_type = self._detect_media_type(file_path)

            # Set video widget visibility
            if self._video_widget:
                self._video_widget.setVisible(self._is_video)

            # Load media
            url = QUrl.fromLocalFile(str(file_path))
            self._media_player.setSource(url)

            self._emit_loading_progress(50)

            # Enable controls
            self._play_btn.setEnabled(True)
            self._stop_btn.setEnabled(True)
            self._progress_slider.setEnabled(True)

            self._emit_loading_progress(100)
            self._emit_loading_finished()

            return True

        except Exception as e:
            self._emit_error(f"Failed to load media: {str(e)}")
            return False

    def load_from_data(self, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Load media from raw data

        Args:
            data: Media data as bytes
            metadata: Optional metadata (should include filename for type detection)

        Returns:
            True if loaded successfully
        """
        try:
            self._emit_loading_started()

            if self._fallback_mode:
                self._emit_loading_progress(100)
                self._emit_error("Media playback not available in fallback mode")
                return False

            self._emit_loading_progress(50)
            self._emit_error("Media data loading not yet implemented")
            return False

        except Exception as e:
            self._emit_error(f"Failed to load media data: {str(e)}")
            return False

    def play_pause(self):
        """Toggle play/pause"""
        if not self._media_player or self._fallback_mode:
            return

        if self._media_player.playbackState() == QMediaPlayer.PlayingState:
            self._media_player.pause()
        else:
            self._media_player.play()

    def play(self):
        """Start playback"""
        if self._media_player and not self._fallback_mode:
            self._media_player.play()

    def pause(self):
        """Pause playback"""
        if self._media_player and not self._fallback_mode:
            self._media_player.pause()

    def stop(self):
        """Stop playback"""
        if self._media_player and not self._fallback_mode:
            self._media_player.stop()

    def seek(self, position: int):
        """
        Seek to position

        Args:
            position: Position in milliseconds
        """
        if self._media_player and not self._fallback_mode:
            self._media_player.setPosition(position)

    def set_volume(self, volume: int):
        """
        Set volume level

        Args:
            volume: Volume level (0-100)
        """
        if self._volume_slider:
            self._volume_slider.setValue(volume)

    def set_playback_rate(self, rate: float):
        """
        Set playback speed

        Args:
            rate: Playback rate (e.g., 1.0 = normal, 2.0 = 2x)
        """
        if self._media_player and not self._fallback_mode:
            self._media_player.setPlaybackRate(rate)

    def get_duration(self) -> int:
        """
        Get media duration

        Returns:
            Duration in milliseconds
        """
        return self._duration

    def get_position(self) -> int:
        """
        Get current playback position

        Returns:
            Position in milliseconds
        """
        return self._position

    def is_playing(self) -> bool:
        """
        Check if media is playing

        Returns:
            True if playing
        """
        if self._media_player:
            return self._media_player.playbackState() == QMediaPlayer.PlayingState
        return False

    def clear(self) -> None:
        """Clear viewer content"""
        if self._media_player and not self._fallback_mode:
            self._media_player.stop()
            self._media_player.setSource(QUrl())

        self._play_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._progress_slider.setEnabled(False)
        self._progress_slider.setRange(0, 0)
        self._time_current.setText("00:00")
        self._time_total.setText("00:00")

        self._content = None
        self._file_path = None
        self._duration = 0
        self._position = 0

    def get_content_type(self) -> str:
        """
        Get supported content type

        Returns:
            Media content type
        """
        return 'video/*, audio/*'

    def has_content(self) -> bool:
        """
        Check if viewer has content

        Returns:
            True if media is loaded
        """
        if self._fallback_mode:
            return False
        return self._media_player is not None and self._file_path is not None

    def get_widget(self) -> Optional[QWidget]:
        """Get viewer widget"""
        return self._widget

    @staticmethod
    def supports_zoom() -> bool:
        """Check if viewer supports zoom"""
        return False

    def _apply_styles(self):
        """Apply component styles"""
        if self._widget:
            self._widget.setStyleSheet("""
                #media_controls {
                    background-color: palette(window);
                    border-top: 1px solid palette(mid);
                }
                #media_frame {
                    background-color: #000;
                }
                #video_widget {
                    background-color: #000;
                }
                #time_label {
                    font-family: monospace;
                    font-size: 10pt;
                }
            """)
