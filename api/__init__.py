"""FastAPI web layer for CSCN_portal.

Exposes the existing application services as a JSON REST API and serves the
React/Vite single-page app. The whole domain/repository/service stack is reused
unchanged; only the presentation layer (formerly Qt) is replaced.
"""
