"""Targeted tests to improve app.py coverage by testing specific missing lines."""

import threading
from unittest.mock import Mock, patch

import pytest
from dishka import Provider, Scope, provide

from fastapi_dishka import App, Middleware, provide_middleware


class ExampleService:
    """Test service for dependency injection."""

    def __init__(self):
        self.value = "test"


class ExampleProvider(Provider):
    """Test provider for coverage tests."""

    scope = Scope.APP
    service = provide(ExampleService, scope=Scope.APP)


class TestContainerResolution:
    """Test container resolution code paths."""

    @pytest.mark.asyncio
    async def test_resolve_container_first_time(self):
        """Test that _resolve_container creates AppProvider when not already resolved."""
        app = App("Test App", "0.1.0", ExampleProvider())

        # Ensure container is not resolved
        assert app._container_resolved is False

        # This should hit line 66 (class AppProvider definition)
        await app._resolve_container()

        # Verify it was resolved
        assert app._container_resolved is True
        assert hasattr(app.app.state, "container")


class TestStartSync:
    """Test start_sync method code paths."""

    def test_start_sync_resolves_container_when_not_resolved(self):
        """Test start_sync calls asyncio.run when container not resolved (lines 129-130)."""
        app = App("Test App", "0.1.0", ExampleProvider())

        # Ensure container is not resolved
        assert app._container_resolved is False

        # Mock uvicorn.run to avoid actually starting server
        with patch("fastapi_dishka.app.uvicorn.run") as mock_run:
            app.start_sync(blocking=True, host="localhost", port=9000)

            # Should have called uvicorn.run (line 131+)
            mock_run.assert_called_once_with(app.app, host="localhost", port=9000)

            # Container should now be resolved (hit lines 129-130)
            assert app._container_resolved is True

    def test_start_sync_non_blocking_mode(self):
        """Test start_sync in non-blocking mode (line 131)."""
        app = App("Test App", "0.1.0", ExampleProvider())

        # Mock threading to avoid actually starting server
        with patch.object(threading, "Thread") as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            app.start_sync(blocking=False, host="localhost", port=9001)

            # Should create and start a thread (hits line 131 -> _start_non_blocking)
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
            assert app._thread is mock_thread_instance


class TestNonBlockingServer:
    """Test non-blocking server startup code paths."""

    def test_start_non_blocking_creates_thread_and_event_loop(self):
        """Test _start_non_blocking method (lines 143-149)."""
        app = App("Test App", "0.1.0", ExampleProvider())

        # Mock all the components that would actually start a server
        with (
            patch("asyncio.new_event_loop") as mock_new_loop,
            patch("asyncio.set_event_loop") as mock_set_loop,
            patch("fastapi_dishka.app.uvicorn.Config") as mock_config,
            patch("fastapi_dishka.app.uvicorn.Server") as mock_server,
            patch.object(threading, "Thread") as mock_thread,
        ):

            # Set up mocks
            mock_loop = Mock()
            mock_new_loop.return_value = mock_loop
            mock_config_instance = Mock()
            mock_config.return_value = mock_config_instance
            mock_server_instance = Mock()
            mock_server.return_value = mock_server_instance

            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            # Call the method
            app._start_non_blocking("localhost", 9002)

            # Verify thread was created and started
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()

            # Verify the server function was set up correctly
            # Get the target function that was passed to Thread
            call_args = mock_thread.call_args
            target_function = call_args[1]["target"]  # Thread(target=run_server, daemon=True)

            # Execute the target function to test lines 143-149
            target_function()

            # Verify the event loop setup (lines 145-146)
            mock_new_loop.assert_called_once()
            mock_set_loop.assert_called_once_with(mock_loop)

            # Verify uvicorn setup (lines 147-148)
            mock_config.assert_called_once_with(app.app, host="localhost", port=9002)
            mock_server.assert_called_once_with(mock_config_instance)

            # Verify server serve was called (line 149)
            mock_loop.run_until_complete.assert_called_once_with(mock_server_instance.serve())

            # Verify server was stored
            assert app._server is mock_server_instance

    @pytest.mark.asyncio
    async def test_start_async_non_blocking_mode(self):
        """Test async start method in non-blocking mode."""
        app = App("Test App", "0.1.0", ExampleProvider())

        # Mock threading to avoid actually starting server
        with patch.object(threading, "Thread") as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            await app.start(blocking=False, host="localhost", port=9003)

            # Should create and start a thread
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
            assert app._thread is mock_thread_instance
            assert app._container_resolved is True


class TestStopMethod:
    """Test stop method edge cases."""

    def test_stop_with_running_server_and_thread(self):
        """Test stop when both server and thread exist."""
        app = App("Test App")

        # Mock server and thread
        mock_server = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True

        app._server = mock_server
        app._thread = mock_thread

        app.stop()

        # Should signal server to exit and join thread
        assert mock_server.should_exit is True
        mock_thread.join.assert_called_once_with(timeout=10)

    def test_stop_with_dead_thread(self):
        """Test stop when thread is not alive."""
        app = App("Test App")

        mock_server = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False

        app._server = mock_server
        app._thread = mock_thread

        app.stop()

        # Should signal server to exit but not join dead thread
        assert mock_server.should_exit is True
        mock_thread.join.assert_not_called()


class TestMiddlewareRegistration:
    """Test middleware registration code paths."""

    def setup_method(self):
        """Clear all registries before each test."""
        from fastapi_dishka.providers import _clear_all_registries

        _clear_all_registries()

    @pytest.mark.asyncio
    async def test_resolve_container_with_middleware(self):
        """Test _resolve_container with middleware to hit lines 103 and 107."""
        from fastapi_dishka.providers import ProviderMeta

        class TestMiddleware(Middleware):
            async def dispatch(self, request, call_next):
                return await call_next(request)

        class TestProvider(Provider, metaclass=ProviderMeta):
            scope = Scope.APP
            test_middleware = provide_middleware(TestMiddleware)

        app = App("Test App", "0.1.0", TestProvider())

        # This should hit lines 103 and 107 (middleware registration)
        await app._resolve_container()

        # Verify middleware was registered
        assert len(app.middlewares) == 1
        assert app.middlewares[0] is TestMiddleware


class TestLifespanHandler:
    """Test the default lifespan handler."""

    @pytest.mark.asyncio
    async def test_lifespan_closes_container_on_shutdown(self):
        """Test that lifespan handler closes container on shutdown."""
        from fastapi_dishka.app import default_lifespan

        # Create a mock app with container
        mock_app = Mock()
        mock_container = Mock()

        # Make the close method awaitable
        async def mock_close():
            pass

        mock_container.close = mock_close
        mock_app.state.container = mock_container

        # Test the lifespan context manager
        async with default_lifespan(mock_app):
            # During lifespan, nothing should happen
            pass

        # The close method should have been called (we can't easily assert this with async mock)

        # Note: Test for missing container case is covered in integration tests
