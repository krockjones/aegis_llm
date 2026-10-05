# LangGraph → AegisLLM → Hive receipt

This example is the AegisLLM Guard integration for Hive Civilization's live builder bounty. It sends one LangGraph model turn through the local OpenAI-shaped AegisLLM endpoint and attaches `langchain-hive`'s `HiveCallbackHandler`, which mints a publicly verifiable Hive receipt without sending prompt/output text to Hive.

## Prerequisites

1. Start AegisLLM Guard and its Ollama upstream using the repository's normal quickstart.
2. Pull/configure the model named by `AEGISLLM_MODEL` (default: `llama3.2`).
3. If Guard requires an API key, set `AEGISLLM_CLIENT_API_KEY` to one of the configured Guard keys.
4. Set `HIVE_BOUNTY_TAG` to the referrer code returned by Hive bounty registration before the qualifying run.

## One-command qualifying run

From the repository root:

```bash
python -m pip install -r examples/hive_langgraph_receipt/requirements.txt && python examples/hive_langgraph_receipt/run.py
```

Optional overrides:

```bash
export AEGISLLM_OPENAI_BASE_URL=http://127.0.0.1:8765/v1
export AEGISLLM_MODEL=llama3.2
export AEGISLLM_CLIENT_API_KEY=aegis-local-demo
export HIVE_BOUNTY_TAG=bounty_xxxxxxxx
```

A successful run prints the AegisLLM response and Hive's public verification URL. The qualifying artifact should look like:

```text
https://thehiveryiq.com/verify/?id=<receipt_id>
```

That URL, this public Apache-2.0 repository, and the `langgraph` framework are the artifacts used to finalize the Hive bounty claim.

## Privacy boundary

Hive receives receipt metadata and one-way SHA-256 fingerprints. The prompt and model response remain on the local AegisLLM/Ollama path. Do not put API keys, wallet private keys, seed phrases, or other secrets in this example or in a bounty claim.
