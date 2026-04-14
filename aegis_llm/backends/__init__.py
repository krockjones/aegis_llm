"""Upstream adapters for AegisLLM Guard.

Production supports **Ollama only** today. The ``Backend`` protocol and factory
exist for a narrow internal boundary (routes, tests); they are not a
multi-backend product or plugin switch.
"""
