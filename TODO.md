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

- [x] **Prominent staff name & role header** in the New Sale view (a banner
      under the nav shows the on-duty cashier's name and a coloured role badge
      while ringing up; the status bar still shows it too).
- [x] **Empty-state messaging** — friendly hints now appear when the product
      picker, product list, sales list, or staff list is empty (instead of a
      blank tree).

## 🟣 Tech / security

- [x] **Hash stored PINs** — PINs are now PBKDF2-SHA256 hashed with a
      per-PIN salt (`security.py`). Old plaintext PINs are migrated on startup
      (`db._migrate`), and duplicate-PIN checks now compare hashes.
- [x] **Exception log file** — the central error hook writes stack traces to a
      rotating `electronstore.log` (`logutil.py`) for diagnosis on the
      customer's machine.
- [x] **Repository-layer cleanup** — `db.connection()` context manager handles
      open/commit/rollback/close; every operations helper uses it now.

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
- [x] Staff name & role banner in New Sale (w/ empty-state hints)
- [x] Hashed PINs (PBKDF2 + migration), rotating exception log
- [x] Repository-layer cleanup (`db.connection()` context manager)
