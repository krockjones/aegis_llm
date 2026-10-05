# Paraloom bounty report — global swap-job status leaks another approved origin's private-swap result

> **Severity:** Low · **Component:** `paraloom-wallet` · **Reward tier:** up to $50 USDC
> **Analyzed:** wallet `main` @ `1e79eec8fbe99cd7e1381f6971c855bdce883d41` · source-level/local reasoning only · no live chain touched

## Summary

The wallet correctly authorizes `GET_SWAP_STATUS` to **an approved origin**, but the status object it returns is a **single global `swapJob`** that is not bound to the origin that initiated the private swap.

As a result, any site the user previously approved can poll `GET_SWAP_STATUS` while another approved site is running a private swap and receive that other site's job state and completed result.

The completed result includes privacy-sensitive public-chain linkage data:

- the fresh unlinkable Solana address used for the private swap;
- the swap transaction signature;
- the routed output amount;
- whether the output was re-shielded.

This allows one approved dapp to correlate another approved dapp's private-swap activity and fresh address, weakening the privacy boundary the fresh-address design is intended to provide.

## Root cause

`SwapJob` has no owner/origin field:

```ts
interface SwapJob {
  status: "pending" | "done" | "error"
  result?: unknown
  error?: string
  startedAt?: number
}

async function setSwapJob(job: SwapJob): Promise<void> {
  await chrome.storage.session.set({ swapJob: job }).catch(() => {})
}
```

A `PRIVATE_SWAP` request authenticates the caller and starts the global job:

```ts
if (message.type === "PRIVATE_SWAP") {
  isAuthorizedSender(sender).then((ok) => {
    if (!ok) return sendResponse({ success: false, error: "not authorized" })
    void setSwapJob({ status: "pending", startedAt: Date.now() })
    void runSwapJob(message.params, sender)
    sendResponse({ success: true, pending: true })
  })
}
```

But `GET_SWAP_STATUS` checks only whether the polling caller is *some* authorized origin, then returns the same global row:

```ts
if (message.type === "GET_SWAP_STATUS") {
  isAuthorizedSender(sender)
    .then((ok) => {
      if (!ok) return sendResponse(null)
      chrome.storage.session
        .get("swapJob")
        .then((r) => sendResponse(r.swapJob ?? null))
        .catch(() => sendResponse(null))
    })
  return true
}
```

No comparison is made between the polling origin and the origin that created the job.

`runSwapJob()` later writes the result globally:

```ts
const result = await handlePrivateSwap(params)
await setSwapJob({ status: "done", result: result.data })
```

and `handlePrivateSwap()` returns data including:

```ts
{
  freshAddress: result.freshAddress,
  swapSignature: result.swapSignature,
  outAmount: result.outAmount,
  reshielded: result.reshielded !== undefined
}
```

The page bridge polls `GET_SWAP_STATUS` until it sees that global `done` result and returns it to JavaScript.

## Reproduction

This can be reproduced without any live chain transaction by mocking only the runtime-message/storage boundary:

1. User has previously approved two origins, A and B.
2. Origin A starts `PRIVATE_SWAP`; its per-request approval occurs normally.
3. The background worker stores `{ status: "pending" }` in global `swapJob` and later stores a deterministic completed result such as:

```json
{
  "status": "done",
  "result": {
    "freshAddress": "FreshAddressForOriginA",
    "swapSignature": "SwapSignatureForOriginA",
    "outAmount": 12345,
    "reshielded": true
  }
}
```

4. Before or after completion, origin B calls `GET_SWAP_STATUS`.
5. `isAuthorizedSender(B)` succeeds because B is independently approved.
6. The handler returns A's global job/result to B because no origin binding exists.

A control with an unapproved origin correctly returns `null`; the defect is cross-origin isolation among approved dapps.

## Impact

Paraloom private swaps intentionally exit through a fresh, unlinkable address. A different approved dapp learning that fresh address + swap signature can link the user's wallet session to public swap activity it did not initiate.

The information is public once the chain transaction exists, but the sensitive link is **which fresh address belongs to this user's private wallet activity**. The wallet currently gives that correlation directly to any other approved origin.

This matches the Stage-1 Low definition: a **privacy-weakening information leak**. It does not bypass swap approval or move funds.

## Distinct from existing reports

- Existing authorization fixes such as the `#719` family gate individual wallet reads/actions on `isAuthorizedSender`; this report assumes both origins are legitimately approved and shows that the returned job state is not partitioned by origin.
- Existing private-swap reports (#839, #852–#857, #862) cover settlement/accounting/recovery paths, not cross-origin status disclosure.
- Duplicate searches for `GET_SWAP_STATUS`, `swapJob`, origin binding, fresh-address leaks, and private-swap privacy returned no matching bounty report.

## Suggested fix

Bind every swap job to the initiating origin and enforce that binding on reads:

```ts
interface SwapJob {
  origin: string
  status: "pending" | "done" | "error"
  ...
}
```

On `PRIVATE_SWAP`, derive the origin from `sender` and persist it with the job. On `GET_SWAP_STATUS`, derive the caller origin and return the job only when `job.origin === callerOrigin`.

Alternatively store jobs under an origin-keyed namespace rather than one global `swapJob` key. Do not use only `isAuthorizedSender()` as cross-origin isolation: that proves the site is trusted generally, not that it owns this spend/result.

## Scope / safety

- Static/source-level analysis against the public wallet repository.
- No live-chain traffic, third-party funds, spam, or DoS.
- A deterministic reproduction needs only mocked Chrome runtime/storage state.
- AI-assisted analysis used, permitted by the program.

## Payout address

**EVM / USDC:** `0xAcA9ae77726afFAD8963D883864B13f7fB0d7100`
