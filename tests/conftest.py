"""Shared pytest fixtures and configuration for newm tests."""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, Mock

import pytest

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config_dir(temp_dir: Path, monkeypatch) -> Path:
    """Create and set a mock configuration directory."""
    config_dir = temp_dir / "config"
    config_dir.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_dir))
    return config_dir


@pytest.fixture
def mock_cache_dir(temp_dir: Path, monkeypatch) -> Path:
    """Create and set a mock cache directory."""
    cache_dir = temp_dir / "cache"
    cache_dir.mkdir()
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_dir))
    return cache_dir


@pytest.fixture
def mock_runtime_dir(temp_dir: Path, monkeypatch) -> Path:
    """Create and set a mock runtime directory."""
    runtime_dir = temp_dir / "runtime"
    runtime_dir.mkdir()
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime_dir))
    return runtime_dir


@pytest.fixture
def sample_config_file(mock_config_dir: Path) -> Path:
    """Create a sample newm configuration file."""
    config_file = mock_config_dir / "newm" / "config.py"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    config_content = '''
# Sample newm configuration for testing
corner_radius = 20
gaps = 8

def key_bindings(layout):
    return {
        "M-Return": lambda: None,
        "M-q": lambda: None,
    }
'''
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_display():
    """Mock display object for Wayland compositor tests."""
    display = Mock()
    display.get_fd = Mock(return_value=3)
    display.dispatch = Mock(return_value=0)
    display.flush = Mock()
    return display


@pytest.fixture
def mock_dbus_session():
    """Mock D-Bus session for testing D-Bus interactions."""
    session = MagicMock()
    session.register_service = Mock()
    session.publish_object = Mock()
    return session


@pytest.fixture
def mock_pam_handle():
    """Mock PAM handle for authentication tests."""
    handle = Mock()
    handle.authenticate = Mock(return_value=None)
    handle.open_session = Mock()
    handle.close_session = Mock()
    return handle


@pytest.fixture
def mock_cairo_surface():
    """Mock Cairo surface for rendering tests."""
    surface = Mock()
    surface.get_width = Mock(return_value=1920)
    surface.get_height = Mock(return_value=1080)
    surface.write_to_png = Mock()
    return surface


@pytest.fixture
def mock_gesture_event():
    """Mock gesture event for gesture recognition tests."""
    event = Mock()
    event.time = 1000
    event.x = 500
    event.y = 300
    event.dx = 10
    event.dy = 5
    return event


@pytest.fixture
def clean_environment(monkeypatch):
    """Clean environment variables that might affect tests."""
    env_vars_to_remove = [
        "WAYLAND_DISPLAY",
        "DISPLAY",
        "NEWM_CONFIG",
        "NEWM_DEBUG",
    ]
    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests."""
    # This would reset any singleton patterns used in the codebase
    # Add specific singleton resets as needed
    yield


@pytest.fixture
def capture_logs(caplog):
    """Fixture to easily capture and assert on logs."""
    with caplog.at_level("DEBUG"):
        yield caplog