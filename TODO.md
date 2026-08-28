# ElectronStore POS — Remaining To-Dos

A running list of improvements identified in the review, in order of priority.
Tick each off as it is completed. The **top-3** money/ops items are already done
(integer KES, sale voids, cash change + receipts).

---

## 🔴 High priority

- [x] **Product editing** — added edit (price/cost/category/name/code),
      **Restock**, and **Delete** in the Products tab.
- [x] **Pin versions in `requirements.txt`** — now pinned to exact versions.

## 🟡 Operational

- [x] **Per-staff sales log / cash reconciliation report** — new **By Staff**
      report in the Reports tab (transactions, units, revenue per cashier).
- [x] **End-of-day / shift close report** — new **End of Day** report
      (payment-method totals, units sold, voids) for today or any chosen date.
- [x] **Payment-method validation** — `create_sale` now rejects anything other
      than cash/card/mobile.

## 🟢 UX / polish

- [ ] **Prominent staff name & role header** in the New Sale view (status bar
      already shows it, but make cashier identity clearer while ringing up).
- [ ] **Empty-state messaging** — show friendly hints when product/sales lists
      are empty (instead of a blank tree).

## 🟣 Tech / security

- [ ] **Hash stored PINs** — PINs are stored in plaintext in `store.db`. For a
      local POS this is acceptable, but hashing (e.g. PBKDF2/scrypt) would be
      safer. Requires a scheme-version migration.
- [ ] **Exception log file** — central error hook exists (`_error_hook`); write
      stack traces to a rotating log for diagnosis on the customer's machine.
- [ ] **Repository-layer cleanup** — `get_conn()` is reopened in every helper;
      consider a small data-access layer or context manager (non-urgent).

---

### Done (recent batches)

- [x] Integer KES money (whole shillings) with DB migration
- [x] Sale voids (restock + exclude from reports)
- [x] Cash tendered → change + printable receipt
- [x] Per-line discount wired into the New Sale cart
- [x] pytest data-layer suite + pinned/added pytest
- [x] Product editing, restock, delete
- [x] Pinned requirements
- [x] Per-staff and end-of-day reports
- [x] Payment-method validation
