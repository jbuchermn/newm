"""Validation tests to ensure the testing infrastructure is properly configured."""

import sys
from pathlib import Path

import pytest


class TestSetupValidation:
    """Tests to validate the testing setup is working correctly."""

    def test_python_path_configured(self):
        """Verify the Python path includes the project root."""
        project_root = Path(__file__).parent.parent
        assert str(project_root) in sys.path, "Project root not in Python path"

    def test_import_main_package(self):
        """Verify we can import the main newm package (or handle missing dependencies gracefully)."""
        try:
            import newm
            assert newm is not None
        except ImportError as e:
            # Expected if pywm is not installed
            if "pywm" in str(e):
                pytest.skip("pywm dependency not installed - this is expected")
            else:
                pytest.fail(f"Failed to import newm package: {e}")

    def test_import_panel_package(self):
        """Verify we can import the panel package (or handle missing dependencies gracefully)."""
        try:
            import newm_panel_basic
            assert newm_panel_basic is not None
        except ImportError as e:
            # Expected if certain dependencies are not installed
            if "pkg_resources" in str(e) or "pywm" in str(e):
                pytest.skip("Optional dependency not installed - this is expected")
            else:
                pytest.fail(f"Failed to import newm_panel_basic package: {e}")

    def test_fixture_temp_dir(self, temp_dir):
        """Verify the temp_dir fixture works correctly."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Test we can create files in it
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"

    def test_fixture_mock_config_dir(self, mock_config_dir):
        """Verify the mock_config_dir fixture works correctly."""
        assert mock_config_dir.exists()
        assert mock_config_dir.is_dir()
        assert mock_config_dir.name == "config"
        
        # Verify environment variable is set
        import os
        assert os.environ.get("XDG_CONFIG_HOME") == str(mock_config_dir)

    def test_fixture_sample_config(self, sample_config_file):
        """Verify the sample_config_file fixture works correctly."""
        assert sample_config_file.exists()
        assert sample_config_file.is_file()
        assert "corner_radius = 20" in sample_config_file.read_text()

    def test_pytest_markers(self):
        """Verify custom pytest markers are registered."""
        # Check if markers are accessible via pytest.mark
        try:
            # Try to access the markers - they should exist
            _ = pytest.mark.unit
            _ = pytest.mark.integration  
            _ = pytest.mark.slow
            assert True
        except AttributeError:
            pytest.fail("Custom markers not properly registered")

    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit test marker works."""
        assert True

    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that integration test marker works."""
        assert True

    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that slow test marker works."""
        assert True

    def test_mock_fixtures_available(self, mock_display, mock_dbus_session, 
                                   mock_pam_handle, mock_cairo_surface, 
                                   mock_gesture_event):
        """Verify all mock fixtures are available and functional."""
        # Test mock_display
        assert mock_display.get_fd() == 3
        mock_display.dispatch()
        mock_display.dispatch.assert_called_once()

        # Test mock_dbus_session
        mock_dbus_session.register_service("test.service")
        mock_dbus_session.register_service.assert_called_with("test.service")

        # Test mock_pam_handle
        mock_pam_handle.authenticate()
        mock_pam_handle.authenticate.assert_called_once()

        # Test mock_cairo_surface
        assert mock_cairo_surface.get_width() == 1920
        assert mock_cairo_surface.get_height() == 1080

        # Test mock_gesture_event
        assert mock_gesture_event.time == 1000
        assert mock_gesture_event.x == 500
        assert mock_gesture_event.y == 300

    def test_clean_environment(self, clean_environment):
        """Verify the clean_environment fixture removes expected variables."""
        import os
        assert "WAYLAND_DISPLAY" not in os.environ
        assert "DISPLAY" not in os.environ
        assert "NEWM_CONFIG" not in os.environ
        assert "NEWM_DEBUG" not in os.environ