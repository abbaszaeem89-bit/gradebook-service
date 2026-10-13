# gradebook.py -- the department gradebook service
import datetime
import http.server
import json
import logging
import sys

from errors import ConflictError, GradebookError, NotFoundError, ValidationError
from models import parse_assessment, parse_mark, parse_student

logger = logging.getLogger(__name__)

DATA = "gradebook.json"
STATE = {"students": {}, "assessments": {}, "marks": []}


def load():
    global STATE
    try:
        with open(DATA) as f:
            STATE = json.load(f)
    except FileNotFoundError:
        STATE = {"students": {}, "assessments": {}, "marks": []}


def save():
    with open(DATA, "w") as f:
        json.dump(STATE, f)


def pct(sid):
    total = 0.0
    got = 0.0
    for m in STATE["marks"]:
        if m["student"] == sid:
            a = STATE["assessments"].get(m["assessment"])
            if a:
                got = got + float(m["score"]) * float(a["weight"]) / float(a["total"])
                total = total + float(a["weight"])
    if total == 0.0:
        return "0"
    return str(round(got, 2))


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_request(self, handler):
        try:
            status, body = handler()
        except ValidationError as err:
            status, body = 400, {"error": str(err)}
        except NotFoundError as err:
            status, body = 404, {"error": str(err)}
        except ConflictError as err:
            status, body = 409, {"error": str(err)}
        except GradebookError as err:
            status, body = 400, {"error": str(err)}
        except Exception:
            logger.exception("Internal server error")
            status, body = 500, {"error": "internal error"}
        self._send(status, body)

    def handle_get(self):
        if self.path == "/students":
            return 200, list(STATE["students"].values())
        if self.path.startswith("/students/"):
            parts = self.path.split("/")
            if len(parts) != 3 or not parts[2]:
                raise NotFoundError("Invalid student URL")
            sid = parts[2]
            if sid not in STATE["students"]:
                raise NotFoundError(f"Student '{sid}' not found")
            s = dict(STATE["students"][sid])
            s["percentage"] = pct(sid)
            return 200, s
        if self.path == "/assessments":
            return 200, list(STATE["assessments"].values())
        if self.path == "/report":
            out = []
            for sid in STATE["students"]:
                out.append({"id": sid, "name": STATE["students"][sid]["name"], "pct": pct(sid)})
            return 200, out
        raise NotFoundError(f"Route '{self.path}' not found")

    def handle_post(self):
        length_header = self.headers.get("Content-Length", "0")
        try:
            n = int(length_header)
        except ValueError:
            raise ValidationError("Invalid Content-Length header")
        raw = self.rfile.read(n)
        try:
            payload = json.loads(raw)
        except Exception as err:
            raise ValidationError(f"Invalid JSON: {err}") from err

        if self.path == "/students":
            student = parse_student(payload)
            if student.id in STATE["students"]:
                raise ConflictError(f"Student '{student.id}' already exists")
            STATE["students"][student.id] = {
                "id": student.id,
                "name": student.name,
                "joined": str(datetime.datetime.now(datetime.timezone.utc)),
            }
            save()
            return 200, STATE["students"][student.id]

        if self.path == "/assessments":
            assessment = parse_assessment(payload)
            if assessment.id in STATE["assessments"]:
                raise ConflictError(f"Assessment '{assessment.id}' already exists")
            STATE["assessments"][assessment.id] = {
                "id": assessment.id,
                "title": assessment.title,
                "weight": str(assessment.weight),
                "total": str(assessment.total),
            }
            save()
            return 200, STATE["assessments"][assessment.id]

        if self.path == "/marks":
            mark = parse_mark(payload)
            if mark.student not in STATE["students"]:
                raise NotFoundError(f"Student '{mark.student}' not found")
            if mark.assessment not in STATE["assessments"]:
                raise NotFoundError(f"Assessment '{mark.assessment}' not found")
            assessment_record = STATE["assessments"][mark.assessment]
            assessment_total = float(assessment_record["total"])
            if mark.score > assessment_total:
                raise ValidationError(
                    f"Score {mark.score} cannot exceed assessment total {assessment_total}"
                )
            STATE["marks"].append(
                {
                    "student": mark.student,
                    "assessment": mark.assessment,
                    "score": str(mark.score),
                    "at": str(datetime.datetime.now(datetime.timezone.utc)),
                }
            )
            save()
            logger.info("recorded mark for %s score %s", mark.student, mark.score)
            return 200, {"ok": True}

        raise NotFoundError(f"Route '{self.path}' not found")

    def do_GET(self):
        self.handle_request(self.handle_get)

    def do_POST(self):
        self.handle_request(self.handle_post)


def main(argv=sys.argv):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    load()
    port = 8000
    if len(argv) > 1:
        port = int(argv[1])
    logger.info("gradebook on %s", port)
    http.server.HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
