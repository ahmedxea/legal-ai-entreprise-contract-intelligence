"""
OpenTelemetry tracing setup.
Call setup_tracing(app) once during application startup.
Set OTEL_EXPORTER_OTLP_ENDPOINT to export to a collector (Jaeger, Azure Monitor, etc.).
When the env var is absent the SDK falls back to a no-op exporter so local dev works
without any external collector.
"""
import logging
import os

logger = logging.getLogger(__name__)


def setup_tracing(app) -> None:
    """
    Instrument the FastAPI application with OpenTelemetry.
    Attaches a trace ID to every request so correlated log lines can be found
    across frontend, backend, and AI agent calls.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create({"service.name": "lexra-backend"})
        provider = TracerProvider(resource=resource)

        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        if otlp_endpoint:
            # Export to a real collector (Jaeger, Azure Monitor OTLP, etc.)
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            logger.info(f"OTLP tracing export enabled: {otlp_endpoint}")
        else:
            # Development fallback: discard spans silently
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
            exporter = ConsoleSpanExporter()
            logger.info("OTLP endpoint not configured — tracing spans discarded (dev mode)")

        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry FastAPI instrumentation active")

    except ImportError as exc:
        logger.warning(
            f"OpenTelemetry packages not installed — tracing disabled. "
            f"Install opentelemetry-sdk and opentelemetry-instrumentation-fastapi. ({exc})"
        )
    except Exception as exc:
        logger.error(f"Failed to set up tracing: {exc}", exc_info=True)
