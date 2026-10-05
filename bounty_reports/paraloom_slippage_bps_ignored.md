# Paraloom bounty report — dapp-requested private-swap slippage is silently discarded

> **Severity:** Low · **Component:** `paraloom-wallet` + first-party swap router · **Reward tier:** up to $50 USDC
> **Analyzed:** wallet `main` @ `1e79eec8fbe99cd7e1381f6971c855bdce883d41`, core `main` @ `9e8c8e6d403a4793b841ac1c569eefd11d60c9ad` · source-level analysis only

## Summary

The public dapp API accepts a caller-selected `slippageBps`, carries it through the wallet's explicit approval request, and passes it into both private-swap functions — but the value is silently dropped before the first-party routing request.

The router then quotes/builds the swap using its **process-wide `SLIPPAGE_BPS`**, defaulting to **50 bps**, regardless of what the user/dapp requested.

A dapp requesting tighter protection (for example 10 bps) therefore receives a transaction that permits the router-configured 50 bps instead. The wallet gives no indication that the approved/requested limit was ignored.

## Root cause

The page-facing API exposes slippage:

```ts
privateSwap: async (params: {
  outputMint: string
  inputMint?: string
  amountLamports: string
  slippageBps?: number
  reshield?: boolean
}) => { ... }
```

The background request object also retains it:

```ts
interface SwapRequestParams {
  outputMint: string
  inputMint?: string
  amountLamports: string
  slippageBps?: number
  reshield?: boolean
}
```

and `handlePrivateSwap()` passes the requested/default value into the swap implementation:

```ts
params.slippageBps ?? 100
```

Both `privateSwap()` and `privateSwapFromToken()` accept that argument.

However `routeSwap()` sends only:

```json
{
  "input_mint": "...",
  "output_mint": "...",
  "amount": 123,
  "user_public_key": "..."
}
```

There is no slippage field in the wallet-to-router request.

The first-party core router confirms the mismatch: its request type has no per-request slippage and `src/bin/swap_router.rs` constructs `JupiterSwapProvider` using one process-wide value:

```rust
let slippage_bps: u16 = std::env::var("SLIPPAGE_BPS")
    .ok()
    .and_then(|s| s.parse().ok())
    .unwrap_or(50);

let provider = JupiterSwapProvider::new(
    ReqwestJupiterClient::new(jupiter_base_url.clone()),
    submitter,
    slippage_bps,
    platform_fee_bps,
    fee_account.clone(),
)?;
```

`JupiterSwapProvider::quote()` then places `self.slippage_bps` into Jupiter's `slippageBps` query parameter.

Thus the effective protection is server configuration, not the value the dapp/user supplied.

## Reproduction

No live swap is required to demonstrate the contract break:

1. Call the injected API with:

```js
window.paraloom.privateSwap({
  outputMint: "<mint>",
  amountLamports: "100000000",
  slippageBps: 10
})
```

2. Allow the wallet approval flow to proceed.
3. Capture/stub the POST from wallet `routeSwap()` to `/swap/route`.
4. Observe that the body contains no `slippage_bps`/`slippageBps` field.
5. Drive the first-party router with its default environment.
6. Observe the Jupiter quote URL is built with `slippageBps=50`, not 10.

Controls:
- changing the dapp request from 10 to 100 or 500 changes the wallet function argument but not the `/swap/route` JSON shape;
- changing router `SLIPPAGE_BPS` changes the Jupiter request, proving the server-global value is authoritative.

## Impact

- A user/dapp cannot enforce the slippage limit it requested through the published wallet API.
- Tighter-than-router settings are silently weakened (default router: 50 bps).
- Looser-than-router settings are silently tightened, so callers cannot reason about failure/price behavior from their own request.
- The approval surface does not explain that slippage is server-controlled.

This is not claimed as theft or a proof-system break. It is an input/intent validation failure with limited economic impact, fitting the Stage-1 Low class.

## Distinct from existing reports

Recent private-swap bounties cover settlement false positives, asset selection, dropped transaction recovery, token-input recovery, phantom notes, Token-2022 handling, and SPL withdrawal liveness. Duplicate searches for `slippageBps`, ignored slippage, and router slippage found no existing bounty report.

## Suggested fix

Make slippage authority explicit and end-to-end.

Preferred:

1. add a bounded `slippage_bps` field to the router request;
2. validate it server-side against a safe allowed range;
3. pass the validated per-request value into the Jupiter quote/build path;
4. display the exact effective slippage in the wallet approval UI;
5. add a regression test asserting requested slippage reaches Jupiter unchanged after validation.

If slippage is intentionally operator-controlled, remove `slippageBps` from the public wallet API and approval params and expose the actual router policy to the user instead of silently accepting an ignored parameter.

## Scope / safety

- Static/source-level analysis only.
- No live swaps, mainnet interaction, or third-party funds.
- Reproduction can be performed with mocked HTTP boundaries.
- AI-assisted analysis used, permitted by the program.

## Payout address

**EVM / USDC:** `0xAcA9ae77726afFAD8963D883864B13f7fB0d7100`
