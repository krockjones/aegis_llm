# Paraloom bounty report — private token-swap settlement accepts dust ATA balance

> **Severity:** Medium · **Component:** `paraloom-wallet` · **Reward tier:** up to $150 USDC
> **Analyzed:** wallet `main` @ `1e79eec8fbe99cd7e1381f6971c855bdce883d41` · source-level/local reasoning only · no live chain touched

## Summary

`privateSwapFromToken()` decides that its shielded SPL-token withdrawal has settled by polling the fresh input-token ATA until its balance is merely **greater than zero**:

```ts
async function waitForTokenFunding(connection: Connection, ata: PublicKey): Promise<bigint> {
  ...
  const bal = await connection.getTokenAccountBalance(ata)
  const amt = BigInt(bal.value.amount)
  if (amt > 0n) return amt
}
```

That predicate is not causally tied to the shielded withdrawal.

Unlike the native-SOL private-swap path, the token-input flow makes the fresh address and its input-mint ATA observable **before** this settlement check:

1. it withdraws `GAS_LAMPORTS` of shielded SOL to the fresh address;
2. it creates the input-mint ATA on-chain at that fresh address;
3. only then does it submit the shielded token withdrawal and call `waitForTokenFunding()`.

An unrelated transfer of even one base unit of the input token into that ATA can therefore make `confirmSettled` return `true` while the real shielded token withdrawal is still pending or ultimately fails.

`runTransactFlow()` then treats the shielded spend as settled: it persists change and marks the selected token input notes spent locally. `privateSwapFromToken()` also assigns that unrelated balance to `tokenLanded` and routes **that amount** into the swap leg.

## Reachable sequence

A deterministic local/devnet reproduction is:

1. Start a token-input private swap (for example shielded USDC -> another token) with a fresh address `F`.
2. Allow the gas-withdraw leg to settle and the wallet to create `F`'s USDC ATA. At this point `F` and the ATA are public on-chain.
3. Submit the shielded token-withdraw request, but hold/delay the real settlement so its token transfer has not reached the ATA yet.
4. Before the next `waitForTokenFunding()` poll, transfer `1` base unit of the same input mint from an unrelated account to `F`'s ATA.
5. The next poll observes `amt === 1n` and returns it.
6. `confirmSettled` returns `true`; `runTransactFlow()` books the shielded spend as settled and marks the selected token notes spent locally, even though the intended withdraw has not funded the ATA.
7. `privateSwapFromToken()` calls `routeSwap(..., tokenLanded, inputMint)` with `tokenLanded === 1n`, i.e. the unrelated dust amount rather than the requested withdrawal amount.
8. If that dust-sized route/swap fails and the real withdrawal later lands, the actual input tokens remain at the fresh input-mint ATA.

No production/mainnet interference is required to demonstrate the predicate: the RPC can be mocked so the ATA reports `0`, then `1`, while the protocol settlement/output commitment remains absent.

## Why this is externally triggerable

The fresh key itself remains secret, but secrecy of the key does not prevent third parties from **sending tokens to its public ATA**.

For the token-input flow the fresh public key is revealed by the prior gas withdrawal, and the input-mint ATA is then explicitly created on-chain before the token-withdraw settlement poll starts. Anyone observing those transactions can fund that ATA without the fresh private key.

## Impact

- Shielded token inputs can be marked `spent` locally before the intended withdrawal is proven to have landed.
- Change can be booked from a false settlement decision.
- The private-swap router receives an unrelated dust balance as `tokenLanded`, so the intended token swap can fail or operate on the wrong amount.
- If the real withdrawal later arrives, the actual input token can be left at the fresh ATA instead of being swapped.
- The wallet's normal recovery is especially problematic for this state: the early `SwapOutput` persists `outputMint` but not `inputMint`, so recovery cannot positively identify the stranded input-token balance. (#855 covers that separate post-withdraw recovery defect.)

The fresh key is persisted before the flow, so this does **not** claim cryptographic theft or irrecoverable loss. It fits the program's Medium examples: incorrect accounting plus a recoverable but confusing/liveness-breaking state.

## Distinct from existing reports

- **#839**: manual SOL withdraw uses `recipient SOL balance > before`. Its report explicitly states `privateSwap.ts` was not affected because a freshly generated address was assumed not externally fundable. This report is specifically the **token-input** private-swap path, where the wallet first publicly funds the fresh address and creates the input ATA, making unsolicited token funding possible before `waitForTokenFunding()` runs.
- **#855**: assumes the token withdrawal already landed and shows that later recovery mistakes leftover gas SOL for swap state because `inputMint` is not persisted. This report happens **earlier**: settlement itself is falsely accepted before the intended token withdrawal lands because `waitForTokenFunding()` accepts any positive ATA balance.
- **#856**: concerns a submitted swap transaction being persisted as completed before confirmation. This report occurs before the swap leg is validly funded/submitted.

## Suggested fix

Do not use `ATA balance > 0` as protocol settlement authority.

Prefer confirmation tied to the exact shielded spend (for example the spend/output commitment or another protocol-owned settlement receipt), as the shielded transfer path already does. If an ATA balance observation remains as a secondary signal, bind it to a pre-withdraw baseline and the expected protocol result, but note that even an exact balance delta alone is not causal if arbitrary third parties can fund the ATA.

Also persist the input mode/mint for token-input swap rows so any interrupted flow can reconcile the actual landed input asset independently of the output-side recovery logic.

## Scope / safety

- Static/source-level analysis against the public wallet repository.
- No mainnet attack, spam, DoS, or third-party funds.
- Reproduction can be performed entirely with mocked RPC/local devnet and researcher-owned accounts.
- AI-assisted analysis used, permitted by the program.

## Payout address

**EVM / USDC:** `0xAcA9ae77726afFAD8963D883864B13f7fB0d7100`
