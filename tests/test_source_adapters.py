"""Tests for real source adapter fetch() implementations with mocked HTTP."""
import json
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from earth1.receiver import (
    GDELTAdapter, ACLEDAdapter, FREDAdapter, GoogleTrendsAdapter,
    GeoScope,
)


class TestGDELTFetch:
    def test_successful_fetch(self):
        adapter = GDELTAdapter()
        scope = GeoScope.national("US")

        mock_data = [
            {"tone": 2.5, "url": "http://example.com/1"},
            {"tone": -1.0, "url": "http://example.com/2"},
            {"tone": 0.5, "url": "http://example.com/3"},
        ]

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            reading = adapter.fetch(scope)

        assert reading.status == "ok"
        assert reading.confidence > 0
        assert reading.raw_value == pytest.approx(2.0 / 3.0, abs=0.01)

    def test_empty_response(self):
        adapter = GDELTAdapter()
        scope = GeoScope.national("US")

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([]).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            reading = adapter.fetch(scope)

        assert reading.status == "ok"
        assert reading.raw_value == 0.0
        assert reading.confidence == 0.0

    def test_network_error_graceful(self):
        adapter = GDELTAdapter()
        scope = GeoScope.national("US")

        with patch("urllib.request.urlopen", side_effect=ConnectionError("timeout")):
            reading = adapter.fetch(scope)

        assert reading.status == "error"
        assert reading.confidence == 0.0

    def test_to_forces_with_error_reading(self):
        adapter = GDELTAdapter()
        scope = GeoScope.national("US")

        with patch("urllib.request.urlopen", side_effect=ConnectionError):
            reading = adapter.fetch(scope)
            activation = adapter.to_forces(reading)

        assert activation.forces.sum() == 0.0
        assert activation.confidence.sum() == 0.0

    def test_to_forces_delegates_to_from_values(self):
        adapter = GDELTAdapter()
        scope = GeoScope.national("US")

        mock_data = [{"tone": 3.0} for _ in range(50)]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            reading = adapter.fetch(scope)
            activation = adapter.to_forces(reading)

        assert activation.source_id == "gdelt"


class TestACLEDFetch:
    def test_successful_fetch(self):
        adapter = ACLEDAdapter()
        scope = GeoScope.national("US")

        mock_data = {
            "data": [
                {"event_type": "Protests", "fatalities": 0},
                {"event_type": "Violence against civilians", "fatalities": 3},
                {"event_type": "Protests", "fatalities": 0},
            ]
        }

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            reading = adapter.fetch(scope)

        assert reading.status == "ok"
        assert reading.raw_value == 3.0

    def test_network_error_graceful(self):
        adapter = ACLEDAdapter()
        scope = GeoScope.national("NG")

        with patch("urllib.request.urlopen", side_effect=TimeoutError):
            reading = adapter.fetch(scope)

        assert reading.status == "error"

    def test_to_forces_error_reading(self):
        adapter = ACLEDAdapter()
        scope = GeoScope.national("US")

        with patch("urllib.request.urlopen", side_effect=ConnectionError):
            reading = adapter.fetch(scope)
            activation = adapter.to_forces(reading)

        assert activation.forces.sum() == 0.0


class TestFREDFetch:
    def test_no_api_key_returns_error(self):
        adapter = FREDAdapter()
        scope = GeoScope.national("US")

        with patch.dict("os.environ", {}, clear=True):
            reading = adapter.fetch(scope)

        assert reading.status == "error"

    def test_successful_fetch(self):
        adapter = FREDAdapter()
        scope = GeoScope.national("US")

        def mock_urlopen(req, timeout=None):
            resp = MagicMock()
            resp.read.return_value = json.dumps({
                "observations": [{"date": "2025-01-01", "value": "72.5"}]
            }).encode()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                reading = adapter.fetch(scope)

        assert reading.status == "ok"
        assert reading.confidence > 0

    def test_network_error_graceful(self):
        adapter = FREDAdapter()
        scope = GeoScope.national("US")

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            with patch("urllib.request.urlopen", side_effect=ConnectionError):
                reading = adapter.fetch(scope)

        assert reading.status == "error"

    def test_to_forces_delegates(self):
        adapter = FREDAdapter()
        scope = GeoScope.national("US")

        def mock_urlopen(req, timeout=None):
            resp = MagicMock()
            resp.read.return_value = json.dumps({
                "observations": [{"date": "2025-01-01", "value": "80.0"}]
            }).encode()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                reading = adapter.fetch(scope)
                activation = adapter.to_forces(reading)

        assert activation.source_id == "fred"

    def test_dot_value_skipped(self):
        adapter = FREDAdapter()
        scope = GeoScope.national("US")

        def mock_urlopen(req, timeout=None):
            resp = MagicMock()
            resp.read.return_value = json.dumps({
                "observations": [{"date": "2025-01-01", "value": "."}]
            }).encode()
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                reading = adapter.fetch(scope)

        assert reading.status == "error"


class TestGoogleTrendsFetch:
    def test_no_pytrends_returns_error(self):
        adapter = GoogleTrendsAdapter()
        scope = GeoScope.national("US")

        with patch.dict("sys.modules", {"pytrends": None, "pytrends.request": None}):
            import importlib
            reading = adapter.fetch(scope)

        assert reading.status == "error"

    def test_successful_fetch_mocked(self):
        adapter = GoogleTrendsAdapter()
        scope = GeoScope.national("US")

        mock_df = MagicMock()
        mock_df.empty = False
        mock_col_slice = MagicMock()
        mock_col_slice.mean.return_value = MagicMock(mean=MagicMock(return_value=40.0))
        mock_df.__getitem__ = MagicMock(return_value=mock_col_slice)

        mock_pytrends_instance = MagicMock()
        mock_pytrends_instance.interest_over_time.return_value = mock_df

        mock_request_module = MagicMock()
        mock_request_module.TrendReq.return_value = mock_pytrends_instance

        import sys
        saved = {}
        for k in ["pytrends", "pytrends.request"]:
            saved[k] = sys.modules.get(k)
        sys.modules["pytrends"] = MagicMock()
        sys.modules["pytrends.request"] = mock_request_module

        try:
            reading = adapter.fetch(scope)
        finally:
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v

        assert reading.status == "ok"
        assert reading.confidence == 0.7
        assert reading.raw_value > 0

    def test_pytrends_exception_graceful(self):
        adapter = GoogleTrendsAdapter()
        scope = GeoScope.national("US")

        mock_module = MagicMock()
        mock_module.TrendReq.side_effect = Exception("rate limited")

        with patch.dict("sys.modules", {"pytrends": MagicMock(), "pytrends.request": mock_module}):
            reading = adapter.fetch(scope)

        assert reading.status == "error"

    def test_to_forces_with_error(self):
        adapter = GoogleTrendsAdapter()
        scope = GeoScope.national("US")

        with patch.dict("sys.modules", {"pytrends": None, "pytrends.request": None}):
            reading = adapter.fetch(scope)
            activation = adapter.to_forces(reading)

        assert activation.forces.sum() == 0.0


class TestFromValuesFallback:
    """Ensure all adapters still work via from_values() for offline/simulated mode."""

    def test_gdelt_from_values(self):
        adapter = GDELTAdapter()
        activation = adapter.from_values(tone=-3.0, event_count=500, conflict_intensity=2.5)
        assert activation.source_id == "gdelt"

    def test_acled_from_values(self):
        adapter = ACLEDAdapter()
        activation = adapter.from_values(
            fatalities=10, protest_events=50, violence_events=20)
        assert activation.source_id == "acled"

    def test_fred_from_values(self):
        adapter = FREDAdapter()
        activation = adapter.from_values(
            unemployment=4.2, inflation=3.1, consumer_confidence=72.0, vix=18.5)
        assert activation.source_id == "fred"

    def test_google_trends_from_values(self):
        adapter = GoogleTrendsAdapter()
        activation = adapter.from_values(
            fear_terms=60, desire_terms=45, identity_terms=30)
        assert activation.source_id == "google_trends"
