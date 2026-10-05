# Paraloom bounty report — re-shield recovery can accept an unrelated deposit transaction

> **Severity:** Medium · **Component:** `paraloom-wallet` · **Reward tier:** up to $150 USDC
> **Analyzed:** wallet `main` @ `1e79eec8fbe99cd7e1381f6971c855bdce883d41` · source-level/local reasoning only · no live chain touched

## Summary

`recoverReshieldedNote()` tries to recover a missing re-shield note by scanning the 12 newest Solana transactions that mention the swap's fresh public address. It accepts the first Paraloom `deposit_note_spl` instruction it finds, but it does **not** verify that the deposit instruction belongs to that fresh address, uses the swap output mint, or corresponds to this re-shield.

The relevant shape is:

```ts
const pk = new PublicKey(freshAddress)
const sigs = await connection.getSignaturesForAddress(pk, { limit: 12 })
for (const s of sigs) {
  const tx = await connection.getTransaction(s.signature, ...)
  ...
  for (const ix of ixs) {
    const prog = keys[ix.programIdIndex]
    if (!prog || prog.toBase58() !== programId.toBase58()) continue
    ...
    if (data.length < 80 || !bytesStartWith(data, DEPOSIT_NOTE_SPL_DISCRIMINATOR)) continue
    const amount = dv.getBigUint64(8, true)
    const blinding = data.slice(48, 80)
    return { amount: amount.toString(), blindingHex: ..., signature: s.signature }
  }
}
```

The function never checks the `deposit_note_spl` account list. Merely causing a transaction to mention the victim fresh address is enough for that transaction to enter the scan set.

`recoverReshields()` then treats the returned amount/blinding/signature as the victim's missing re-shield, derives the asset from the *locally recorded output mint*, persists a local shielded note, and writes `reshieldRecovered: true`.

## Reachable poisoning sequence

A local/devnet reproduction can use researcher-owned accounts only:

1. Create a private swap with `reshield: true` and reach the recovery state where the swap output row has a non-empty `swapSignature`, an output mint, and `reshieldRecovered !== true`.
2. Simulate the normal failure case recovery exists for: the genuine `deposit_note_spl` has landed on-chain but the local note was not persisted, or the deposit is still pending recovery.
3. From a separate researcher-owned key, build one Solana transaction that:
   - sends a nominal amount (for example 1 lamport) to the victim fresh address, so the fresh address is in the transaction account keys and `getSignaturesForAddress(fresh)` returns it; and
   - performs the attacker's own valid Paraloom `deposit_note_spl` using attacker-controlled amount/blinding.
4. Ensure this transaction is newer than the genuine re-shield transaction (or mock the RPC to return it first).
5. Run `recoverReshields()`.
6. `recoverReshieldedNote()` sees the attack transaction because it mentions the fresh address, finds the unrelated `deposit_note_spl`, and returns the attacker's amount/blinding/signature without checking that the fresh address was the depositor or that the instruction mint matches the swap.
7. `recoverReshields()` persists those fields as a note for the victim shielded account and marks the swap row `reshieldRecovered: true`.

This can be reproduced hermetically with mocked `getSignaturesForAddress()` / `getTransaction()` responses; no live network interference is required.

## Why the poisoned local note is not self-healing

`persistReshieldedNote()` stores the recovered note as a deposit note with:

- amount from the unrelated instruction;
- blinding from the unrelated instruction;
- asset/mint from the victim swap's local `outputMint`;
- signature from the unrelated transaction;
- **no commitment and no leafIndex**.

At spend time, `ensureLeafIndex()` recomputes the note commitment using the victim's spend public key plus the poisoned amount/blinding/asset and searches the on-chain tree. That commitment was never appended by the attacker's deposit, so the note cannot be spent and fails with `note commitment not found in the on-chain tree`.

The existing phantom-note cleanup does not repair this recovered note because it only investigates notes that already have a non-empty `commitment`. The poisoned recovered deposit note has none.

Worse, the swap row has already been marked `reshieldRecovered: true`, so later recovery skips it and the genuine missing re-shield note is no longer recovered through this path.

## Impact

- A third party can poison re-shield recovery for an observed fresh address without the fresh private key.
- The wallet records an attacker-controlled phantom shielded balance under the victim's output mint.
- That local note is unspendable and not removed by the existing phantom-note healer.
- `reshieldRecovered: true` suppresses future recovery of the genuine missing note, so real shielded funds can remain invisible in the normal wallet UI until state is manually repaired.
- This is incorrect accounting and a recoverability/liveness failure without claiming on-chain theft, matching the program's Medium class.

## Why the fresh address is observable

Private swaps deliberately withdraw to and transact from a fresh **public** Solana address. The secret key remains local, but the public key appears on-chain in the withdrawal/swap activity. A third party does not need the private key to send a nominal transfer to that public address and thereby make a transaction appear in `getSignaturesForAddress(fresh)`.

## Distinct from existing reports

- **#855**: token-input recovery misclassifies leftover gas and lacks `inputMint`; it does not cover unrelated `deposit_note_spl` transactions poisoning Case A re-shield recovery.
- **#856**: a submitted-but-unconfirmed swap signature disables recovery; this report assumes re-shield recovery actually runs and then accepts the wrong transaction.
- **#862**: Token-2022 program-ID handling; unrelated root cause.
- Duplicate searches for `recoverReshieldedNote`, re-shield poisoning, unrelated deposit signatures, and fresh-address transaction binding returned no matching bounty report.

## Suggested fix

Bind recovery to the exact deposit rather than to "any deposit instruction in a transaction that mentions the fresh address".

At minimum, when decoding a candidate `deposit_note_spl` instruction:

1. parse/validate its full account list;
2. require the expected fresh address to be the actual depositor/authority account in the expected position;
3. require the instruction mint to equal the swap row's `outputMint`;
4. require the shielded recipient/spend key to match the wallet account being recovered;
5. recompute the expected commitment from amount/blinding/asset/recipient and verify that commitment exists on-chain before persisting the note and setting `reshieldRecovered`.

Do not mark `reshieldRecovered: true` until the recovered note is cryptographically/on-chain bound to this swap's intended re-shield.

## Scope / safety

- Static/source-level analysis against the public wallet repository.
- No mainnet attack, spam, DoS, or third-party funds.
- Reproduction can be performed with mocked RPC/local devnet and researcher-owned accounts.
- AI-assisted analysis used, permitted by the program.

## Payout address

**EVM / USDC:** `0xAcA9ae77726afFAD8963D883864B13f7fB0d7100`
