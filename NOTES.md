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
