"""Simple focused tests to improve middleware.py coverage."""

from unittest.mock import AsyncMock, Mock

import pytest
from starlette.responses import Response

from fastapi_dishka import Middleware


class ServiceForMiddleware:
    """Test service for dependency injection testing."""

    def __init__(self):
        self.value = "test_value"


class SimpleTestMiddleware(Middleware):
    """Test middleware for testing default dispatch."""

    pass  # Uses default dispatch implementation


class TestGetDependencyErrorHandling:
    """Test error handling in get_dependency method."""

    @pytest.mark.asyncio
    async def test_get_dependency_raises_error_when_no_container_available(self):
        """Test get_dependency raises AttributeError when no container found (lines 64-69)."""
        middleware = Middleware(Mock())

        # Create mock request and app without any container
        mock_request = Mock()
        mock_app = Mock()

        # Use simple objects without container attributes
        class SimpleState:
            pass

        mock_request.app = mock_app
        mock_request.state = SimpleState()
        mock_app.state = SimpleState()

        # Verify hasattr returns False for both containers
        assert not hasattr(mock_request.state, "dishka_container")
        assert not hasattr(mock_app.state, "container")

        # Should raise AttributeError (lines 64-69)
        with pytest.raises(AttributeError, match="No dishka container found"):
            await middleware.get_dependency(mock_request, ServiceForMiddleware)

    @pytest.mark.asyncio
    async def test_get_dependency_falls_back_to_app_container(self):
        """Test get_dependency falls back to app container when request container unavailable (line 81)."""
        middleware = Middleware(Mock())

        # Create mock request without request container but with app container
        mock_request = Mock()
        mock_app = Mock()

        # Use simple classes for state objects
        class RequestState:
            pass  # No dishka_container attribute

        class AppState:
            def __init__(self):
                self.container = AsyncMock()

        mock_request.app = mock_app
        mock_request.state = RequestState()
        mock_app.state = AppState()

        # Set up app container response
        test_service = ServiceForMiddleware()
        mock_app.state.container.get.return_value = test_service

        # Verify request container doesn't exist but app container does
        assert not hasattr(mock_request.state, "dishka_container")
        assert hasattr(mock_app.state, "container")

        # Should use app container fallback (line 81)
        result = await middleware.get_dependency(mock_request, ServiceForMiddleware)

        assert result is test_service
        mock_app.state.container.get.assert_called_once_with(ServiceForMiddleware)


class TestDefaultDispatchBehavior:
    """Test default dispatch method behavior."""

    @pytest.mark.asyncio
    async def test_default_dispatch_calls_next_middleware(self):
        """Test default dispatch implementation calls next middleware (line 98)."""
        middleware = SimpleTestMiddleware(Mock())

        # Create mock request and call_next function
        mock_request = Mock()
        mock_response = Response("test response")

        async def mock_call_next(request):
            return mock_response

        # Should call next middleware and return its response (line 98)
        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result is mock_response


class TestContainerAssertions:
    """Test container assertion edge cases."""

    @pytest.mark.asyncio
    async def test_middleware_container_assertion_with_none_container(self):
        """Test container assertion when container is None."""
        middleware = Middleware(Mock())

        # Create mock with container attribute but set to None
        mock_request = Mock()
        mock_app = Mock()

        class RequestStateWithNone:
            def __init__(self):
                self.dishka_container = None

        class AppState:
            pass

        mock_request.app = mock_app
        mock_request.state = RequestStateWithNone()
        mock_app.state = AppState()

        # Should raise AssertionError due to None container
        with pytest.raises(AssertionError):
            await middleware.get_dependency(mock_request, ServiceForMiddleware)

    @pytest.mark.asyncio
    async def test_middleware_app_container_assertion_with_none(self):
        """Test app container assertion when it's None."""
        middleware = Middleware(Mock())

        # Create mock without request container but app container is None
        mock_request = Mock()
        mock_app = Mock()

        class RequestState:
            pass  # No dishka_container

        class AppStateWithNone:
            def __init__(self):
                self.container = None

        mock_request.app = mock_app
        mock_request.state = RequestState()
        mock_app.state = AppStateWithNone()

        # Should raise AssertionError due to None app container
        with pytest.raises(AssertionError):
            await middleware.get_dependency(mock_request, ServiceForMiddleware)
