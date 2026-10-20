# Task 2: Breaking the Service

This document records the commands, responses, and server errors observed when testing the legacy `gradebook.py` service with malformed or edge-case inputs.

---

## 1. Test Requests and Observations

### (a) Request: `GET /students/NOPE`

* **Command:**
  ```bash
  curl -i http://localhost:8000/students/NOPE
  ```
* **Result:**
  * **HTTP Status Code:** `200 OK`
  * **Response Body:**
    ```json
    {"error": "not found"}
    ```
* **Server Window Error:**
  * None. The server returned HTTP 200 instead of a standard HTTP 404 Not Found error.
* **Analysis:**
  * The legacy service returns HTTP 200 OK even for requests to missing resources, violating REST conventions. Callers cannot rely on HTTP status codes to detect errors.

---

### (b) Request: `POST /students` with body `5`

* **Command:**
  ```bash
  curl -i -X POST http://localhost:8000/students -H "Content-Type: application/json" -d "5"
  ```
* **Result:**
  * **Status / Reply:** `no reply` (Remote end closed connection without response / HTTP 500 socket drop)
* **Server Window Error:**
  ```text
  Exception occurred during processing of request from ('127.0.0.1', 59969)
  Traceback (most recent call last):
    File "...\http\server.py", line 424, in handle_one_request
      method()
    File "...\gradebook.py", line 89, in do_POST
      if "id" not in d or d["id"] == "":
         ^^^^^^^^^^^^^
  TypeError: argument of type 'int' is not iterable
  ```
* **Analysis:**
  * `json.loads("5")` parses into the Python integer `5`. The code assumes the deserialized payload is a `dict` and executes `"id" not in d`. In Python, checking membership in an integer raises an unhandled `TypeError`, crashing request handling.

---

### (c) Request: Create student `S1` and assessment `A1`, POST mark with score `"abc"`, then `GET /students/S1`

* **Commands:**
  ```bash
  curl -i -X POST http://localhost:8000/students -H "Content-Type: application/json" -d '{"id":"S1","name":"Ayesha"}'
  curl -i -X POST http://localhost:8000/assessments -H "Content-Type: application/json" -d '{"id":"A1","title":"Quiz 1","weight":"10","total":"20"}'
  curl -i -X POST http://localhost:8000/marks -H "Content-Type: application/json" -d '{"student":"S1","assessment":"A1","score":"abc"}'
  curl -i http://localhost:8000/students/S1
  ```
* **Result:**
  * `POST /students`: HTTP 200 OK
  * `POST /assessments`: HTTP 200 OK
  * `POST /marks`: HTTP 200 OK `{"ok": true}` (accepted without validating numeric type)
  * `GET /students/S1`: `no reply` (connection dropped without HTTP response)
* **Server Window Error:**
  ```text
  Exception occurred during processing of request from ('127.0.0.1', 59978)
  Traceback (most recent call last):
    ...
    File "...\gradebook.py", line 65, in do_GET
      s["percentage"] = pct(sid)
                        ^^^^^^^^
    File "...\gradebook.py", line 39, in pct
      got = got + float(m["score"]) * float(a["weight"]) / float(a["total"])
                  ^^^^^^^^^^^^^^^^^
  ValueError: could not convert string to float: 'abc'
  ```
* **Analysis:**
  * The mark handler accepts non-numeric string `"abc"` as score and persists it directly into `gradebook.json`. When `GET /students/S1` later calls `pct("S1")`, `float("abc")` crashes with an unhandled `ValueError`.

---

### (d) Request: Stop service, delete `gradebook.json`, restart, create `S1`, create assessment with total `"0"`, add mark, then `GET /report`

* **Commands:**
  ```bash
  # Stop service, remove gradebook.json, restart service
  curl -i -X POST http://localhost:8000/students -H "Content-Type: application/json" -d '{"id":"S1","name":"Ayesha"}'
  curl -i -X POST http://localhost:8000/assessments -H "Content-Type: application/json" -d '{"id":"A1","title":"Quiz 1","weight":"10","total":"0"}'
  curl -i -X POST http://localhost:8000/marks -H "Content-Type: application/json" -d '{"student":"S1","assessment":"A1","score":"10"}'
  curl -i http://localhost:8000/report
  ```
* **Result:**
  * `POST /students`: HTTP 200 OK
  * `POST /assessments`: HTTP 200 OK
  * `POST /marks`: HTTP 200 OK
  * `GET /report`: `no reply` (connection dropped without HTTP response)
* **Server Window Error:**
  ```text
  Exception occurred during processing of request from ('127.0.0.1', 59986)
  Traceback (most recent call last):
    ...
    File "...\gradebook.py", line 74, in do_GET
      out.append({"id": sid, "name": STATE["students"][sid]["name"], "pct": pct(sid)})
                                                                            ^^^^^^^^
    File "...\gradebook.py", line 39, in pct
      got = got + float(m["score"]) * float(a["weight"]) / float(a["total"])
                  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~
  ZeroDivisionError: float division by zero
  ```
* **Analysis:**
  * Assessments accept total `"0"` without validation. In `pct()`, calculating percentage divides by `float(a["total"])`, resulting in an unhandled `ZeroDivisionError` that crashes `/report`.

---

### (e) Request: Delete `gradebook.json` again, restart, then POST a mark for an assessment that does not exist

* **Commands:**
  ```bash
  # Stop service, remove gradebook.json, restart service
  curl -i -X POST http://localhost:8000/students -H "Content-Type: application/json" -d '{"id":"S1","name":"Ayesha"}'
  curl -i -X POST http://localhost:8000/marks -H "Content-Type: application/json" -d '{"student":"S1","assessment":"DOES_NOT_EXIST","score":"10"}'
  ```
* **Result:**
  * If student `S1` exists: HTTP 200 OK `{"ok": true}`
  * If student does not exist: HTTP 200 OK `{"error": "no such student"}`
* **Server Window Error:**
  * None.
* **Analysis:**
  * The `/marks` endpoint checks `if d["student"] not in STATE["students"]`, but never validates whether `d["assessment"]` exists in `STATE["assessments"]`. It accepts orphan marks for non-existent assessments, corrupting data integrity. In `pct()`, `a = STATE["assessments"].get(...)` returns `None`, silently ignoring the mark calculation.

---

## 2. Why We Had to Delete `gradebook.json`

In requests (c) and (d), invalid data (`score: "abc"` and `total: "0"`) was accepted by `do_POST` and immediately committed to persistent storage in `gradebook.json` via `save()`.

Because `load()` reads `gradebook.json` upon startup without schema validation, the poisoned state is restored every time the service starts. Any subsequent request querying the student (`/students/S1`) or requesting a report (`/report`) triggers `pct()` and crashes the server with `ValueError` or `ZeroDivisionError`.

Because there were no administrative endpoints or sanity checks to purge invalid records from disk, deleting `gradebook.json` was the only way to recover the service from the corrupted database.

---

## 3. Bare Excepts Identified by Ruff

Running `ruff check .` identifies 3 bare `except:` clauses:

1. **Line 19 in `load()`:**
   ```python
   except:
       STATE = {"students": {}, "assessments": {}, "marks": []}
   ```
2. **Line 28 in `save()`:**
   ```python
   except:
       pass
   ```
3. **Line 84 in `do_POST()`:**
   ```python
   except:
       self._send(200, {"error": "bad json"})
       return
   ```

### Dangers of Bare `except:`
* Catches `BaseException`, including `KeyboardInterrupt` (Ctrl+C) and `SystemExit`, preventing clean program shutdown.
* Silently swallows unintended bugs such as `NameError`, `TypeError`, disk permission errors (`PermissionError`), or disk full conditions (`OSError`).
* In `save()`, failure to write state to disk is suppressed without warning (`except: pass`), leading to silent data loss.

---

## 4. Task 8: Repeating Task 2 Requests on Refactored Service

After implementing domain exceptions, strict dataclass validation, payload parsers, and the HTTP error boundary in `gradebook.py`, the Task 2 requests were repeated against the updated service.

### Summary Comparison Table

| Case | Request Description | Legacy Behavior | Refactored Behavior | Status Code |
| :--- | :--- | :--- | :--- | :--- |
| **(a)** | `GET /students/NOPE` | `200 {"error": "not found"}` | `404 {"error": "Student 'NOPE' not found"}` | **404 Not Found** |
| **(b)** | `POST /students` body `5` | Server unhandled `TypeError`, socket dropped (`no reply`) | `400 {"error": "Student payload must be a dict"}` | **400 Bad Request** |
| **(c)** | `POST /marks` score `"abc"` then `GET /students/S1` | Accepted bad data (`200`), state corrupted; `GET` crashed with unhandled `ValueError` (`no reply`) | Rejected immediately with `400 {"error": "Field 'score' must be a valid number, got 'abc'"}`; `GET /students/S1` returns `200` intact | **400 Bad Request** |
| **(d)** | `POST /assessments` total `"0"` then `GET /report` | Accepted `0` total (`200`), state corrupted; `GET /report` crashed with `ZeroDivisionError` (`no reply`) | Rejected immediately with `400 {"error": "total must be greater than 0"}`; state remains clean | **400 Bad Request** |
| **(e)** | `POST /marks` for non-existent assessment | Silently recorded orphan mark (`200 {"ok": true}`) | Rejected with `404 {"error": "Assessment 'NONEXISTENT' not found"}` | **404 Not Found** |

### Detailed Results

#### (a) `GET /students/NOPE`
* **Response:** `404 Not Found`
* **Body:** `{"error": "Student 'NOPE' not found"}`
* **Server Window:** Clean request dispatch, no unhandled exceptions.

#### (b) `POST /students` with body `5`
* **Response:** `400 Bad Request`
* **Body:** `{"error": "Student payload must be a dict"}`
* **Server Window:** Error boundary handled validation cleanly, returned 400.

#### (c) `POST /marks` score `"abc"` then `GET /students/S1`
* **Response to POST:** `400 Bad Request`
* **Body:** `{"error": "Field 'score' must be a valid number, got 'abc'"}`
* **Response to GET:** `200 OK`
* **Body:** `{"id": "S1", "name": "Ayesha", "joined": "...", "percentage": "0"}`
* **Server Window:** Bad mark was blocked at input boundary; storage was never corrupted; subsequent student calculation succeeded without crashes.

#### (d) `POST /assessments` total `"0"` then `GET /report`
* **Response to POST:** `400 Bad Request`
* **Body:** `{"error": "total must be greater than 0"}`
* **Server Window:** Model validation stopped zero-total assessment before persistence; `/report` remains error-free.

#### (e) `POST /marks` for non-existent assessment
* **Response:** `404 Not Found`
* **Body:** `{"error": "Assessment 'NONEXISTENT' not found"}`
* **Server Window:** Foreign-key reference verified against `STATE["assessments"]`; orphan mark prevented.

---

# Lab 04 - Proving the tests can fail

I changed the `/` to `*` in `pct()` and ran the tests:
```text
3 failed, 25 passed
```

After undoing the change:
```text
28 passed
```

## Which double is which
- **Stub:** `fixed_now` in `tests/test_add_mark.py`. It always returns the same time (`"2026-10-12 09:00:00"`), so the expected `"at"` value is known.
- **Fake:** the `state` fixture in `tests/conftest.py`. It is a plain dict that works like the real gradebook. The files in `tests/test_storage.py` are real files in `tmp_path`.
- **Mock:** `Mock()` passed as `save` in `tests/test_add_mark.py`. It records the call, so the tests can check `"called once"` and `"not called"`.

## Why I did not mock pct() or the file in Task 5
- `pct()` is plain logic inside my own program. I can call it directly, and mocking it would hide the very calculation under test.
- `tmp_path` gives a real, empty file for each test. Testing `load()` and `save()` against it checks what really happens (JSON written and read back, a missing file, a corrupt file). A mock would only check that I called `open`.

---

# Lab 05: Test-Driven Development and Boundary Cases

## Task 1: Initial Coverage Baseline
* **Initial Test Coverage:** 34% (across all repository files; 44% across core service modules `gradebook.py`, `models.py`, `errors.py`).
* **File with Lowest Coverage:** `gradebook.py` (37% line coverage, 86 statements missed out of 149) among service modules (and helper scripts at 0%).
* **Dependencies Installed:** `hypothesis==6.170.5`, `coverage==7.16.2`, `sortedcontainers==2.4.0`.
* **Configuration:** `.coveragerc` created with branch coverage enabled; `.hypothesis/`, `.coverage`, and `htmlcov/` added to `.gitignore`.

---

## Task 2: Test-Driven Development of ensure_weight_fits

### Cycle 1: `([], 50)` fits
* **Test:** `test_empty_weights_fits` in `tests/test_rules.py`.
* **Failure Message (Red):**
  ```text
  ModuleNotFoundError: No module named 'rules'
  ```
* **Least Code (Green):**
  A new file `rules.py` defining `def ensure_weight_fits(existing_weights, new_weight): pass`.
* **Outcome:** Test passed immediately.

### Cycle 2: `([60], 50)` raises ValidationError with "100" in message
* **Test:** `test_over_100_raises` in `tests/test_rules.py`.
* **Failure Message (Red):**
  ```text
  FAILED tests/test_rules.py::test_over_100_raises - Failed: DID NOT RAISE ValidationError
  ```
* **Least Code (Green):**
  Check `if sum(existing_weights) + new_weight > 100:` and raise `ValidationError("Total weight would be ..., which exceeds the maximum of 100")`.
* **Outcome:** Test passed.

### Cycle 3: `([60], 40)` fits (exactly 100 allowed)
* **Test:** `test_exactly_100_fits` in `tests/test_rules.py`.
* **Did Cycle 3 fail first?**
  **No, Cycle 3 passed at once.** Because Cycle 2 implemented the strict inequality `> 100`, an exact sum of 100 evaluates to `False` for the rejection condition and did not raise an exception. It successfully pinned down the boundary rule without needing a code edit.

### Cycle 4: `([9.3, 27.3, 33.7], 29.7)` fits (floating-point tolerance)
* **Test:** `test_float_tolerance_fits` in `tests/test_rules.py`.
* **Failure Message (Red):**
  ```text
  FAILED tests/test_rules.py::test_float_tolerance_fits - errors.ValidationError: Total weight would be 100, which exceeds the maximum of 100.
  ```
  *Analysis:* In IEEE 754 floating-point arithmetic, `9.3 + 27.3 + 33.7 + 29.7` evaluates to `100.00000000000001`. A strict `> 100` check incorrectly rejected a valid weight sum of 100 on paper.
* **Least Code (Green):**
  Added tolerance `1e-9`: `if total > 100.0 + 1e-9: raise ValidationError(...)`.
* **Outcome:** Test passed.

---

## Task 3: Refactoring rules.py
* **Named Constants:** Extracted `MAX_TOTAL_WEIGHT = 100.0` and `TOLERANCE = 1e-9`.
* **Type Hints:** Added `existing_weights: list[float]`, `new_weight: float`, and `-> None` return type annotation.
* **Docstrings:** Documented module purpose, function contract, tolerance justification, and exception types.
* **Static Verification:**
  * `mypy --strict rules.py` reported: `Success: no issues found in 1 source file`.
  * `ruff check .` reported: `All checks passed!`.

---

## Task 4: Service Integration (add_assessment Seam)
* **Seam Function:** Extracted `add_assessment(state, assessment, save)` in `gradebook.py` to decouple assessment validation, weight enforcement, and persistence from HTTP networking.
* **Test Suite:** `tests/test_add_assessment.py` tests:
  1. Valid assessment is stored in state and calls `save` once.
  2. Overweight assessment (exceeding 100) raises `ValidationError`, stores nothing, and does not call `save`.
  3. Duplicate assessment ID raises `ConflictError`, stores nothing, and does not call `save`.
* **HTTP Endpoint:** Refactored `POST /assessments` in `Handler.handle_post` to call `add_assessment(STATE, assessment, save)`.
* **Manual Verification:**
  * Assessment with weight 60: accepted (HTTP 200).
  * Assessment with weight 40: accepted (HTTP 200, cumulative total 100).
  * Assessment with weight 0.5: rejected (HTTP 400 Bad Request, message: `"Total weight would be 100.5, which exceeds the maximum of 100."`).

---

## Task 5: What Coverage Does and Does Not Tell You
* **Updated Test Coverage:** 34% (56% across core modules `gradebook.py`, `models.py`, `errors.py`, `rules.py`).
* **Weak Test Experiment:**
  * Created `tests/test_weak.py` containing:
    ```python
    def test_weak(loaded):
        import gradebook
        loaded['marks'].append({'student': 'S1', 'assessment': 'A1', 'score': 15.0, 'at': 'now'})
        gradebook.pct('S1')
    ```
  * Running only `tests/test_weak.py` with coverage:
    ```text
    tests/test_weak.py . [100%]
    Name           Stmts   Miss Branch BrPart  Cover   Missing
    gradebook.py     149    110     44      4    23%   pct() lines 34-43 all covered
    ```
    Every line of `pct()` except the guard `return "0"` was covered, despite asserting nothing!
  * Mutating `/` to `*` in `pct()`:
    * `pytest tests/test_weak.py`: PASSED (asserted nothing, so silent bug went undetected).
    * `pytest tests/test_pct.py`: FAILED (3 failed, properly asserting calculation results).
  * Removed `tests/test_weak.py` and restored `/` in `pct()`.
* **Two Sentences on Coverage:**
  1. Coverage tells you exactly which statements and conditional branches were executed while the test suite ran, highlighting dead or unvisited code paths.
  2. Coverage cannot tell you whether those executions were asserted for correctness, whether business invariants were satisfied, or whether defect-ridden logic executed and went completely unchecked.
* **Untested Function in `gradebook.py`:**
  `main(argv)` has no tests covering its CLI argument parsing, port range validation, or server startup logic.

---

## Task 6: Boundary Cases
* **Parametrized Boundaries Tested (`tests/test_boundaries.py`):**
  * Weight boundaries: `0.0` and `100.0` are accepted; `-0.01` and `100.01` are rejected with `ValidationError`.
  * Assessment total boundaries: `0.01` is accepted; `0.0` is rejected with `ValidationError`.
  * Score boundaries: For an assessment with total 20, scores `0.0` and `20.0` are accepted; `-0.01` and `20.01` are rejected and nothing is stored.
* **Mutation Experiment:**
  * Changed `mark.score > assessment_row["total"]` to `mark.score >= assessment_row["total"]` in `add_mark()`.
  * Running `pytest` immediately caught the off-by-one regression.
  * **Failing Boundary Test:** `tests/test_boundaries.py::test_score_accepted[score-at-total-accepted]` failed with `ValidationError: score exceeds assessment total`.
  * Change reverted back to strict `>`.

---

## Task 7: Hypothesis Property-Based Testing
* **Property Test:** `tests/test_properties.py::test_pct_does_not_exceed_weight` using Hypothesis strategy `@given(scores=st.lists(st.integers(min_value=0, max_value=20), min_size=1, max_size=5))`.
* **Shrunk Failing Counterexample Found by Hypothesis:**
  ```text
  Falsifying example: test_pct_does_not_exceed_weight(
      scores=[11, 11],
  )
  ```
* **Explanation of the Defect:**
  `add_mark()` unconditionally appended every mark to `state["marks"]`, allowing multiple duplicate marks for the same student and assessment to accumulate. In `pct()`, points for all recorded marks are summed together without deduplication, causing the calculated percentage to improperly compound and exceed the assessment's maximum weight limit.
* **Strict xfail Annotation:**
  Decorated with `@pytest.mark.xfail(strict=True, reason="duplicate marks are all counted")` so the test suite remained green until the defect was resolved in Task 8.

---

## Task 8: Fixing the Defect and Final Verification
* **Test-First Verification:**
  Added `test_new_mark_replaces_old_mark_for_same_student_and_assessment` in `tests/test_add_mark.py` checking that after recording marks 5 and 18 for the same student and assessment, exactly one mark remains with score 18.
* **Defect Fix:**
  Updated `add_mark()` in `gradebook.py` to filter out any existing mark for that `(student, assessment)` pair before appending the new mark, ensuring all validations precede any state modifications.
* **Xfail Removal:**
  Removed `@pytest.mark.xfail` from `tests/test_properties.py`. With deduplication implemented, the property test passes unconditionally across hundreds of generated score lists.
* **Final Code Quality Verification:**
  * `pytest`: 51 passed in 1.26s.
  * `ruff check .`: All checks passed.
  * `mypy gradebook.py`: Success: no issues found.
  * `mypy --strict errors.py models.py rules.py`: Success: no issues found in 3 source files.
* **Final Coverage Report:**
  * Total statements: 478, Miss: 326, Branch coverage: 34% (core application modules: 56% overall, `rules.py` 100%, `errors.py` 100%, `models.py` 80%, `gradebook.py` 41%).


