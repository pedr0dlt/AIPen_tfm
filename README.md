# TFM Pentesting Autónomo con LLM

Este repositorio complementa mi TFM, cuyo título es **"Desarrollo e implementación de una herramienta basada en LLM para aided pentesting"**

## Arquitectura

- **Ollama**: Proveedor local de modelos de lenguaje (LLM).
- **Orchestrator**: Contenedor en Python (LangGraph) que implementa el ciclo ReAct, gestiona el estado y toma decisiones.
- **Executor**: Contenedor basado en Kali Linux que recibe comandos del Orchestrator vía API REST interna y devuelve los resultados.

## Despliegue

```bash
docker-compose up -d --build
```
