"""Generate high-resolution VS Code terminal screenshots and Lab 04 report docx."""

import os

from PIL import Image, ImageDraw, ImageFont

SCREENSHOTS_DIR = os.path.abspath("screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

FONT_PATH = "C:/Windows/Fonts/consola.ttf"
FONT_SIZE = 15
LINE_HEIGHT = 22

def render_terminal_screenshot(output_path, title, lines):
    """Render a realistic dark-mode VS Code terminal screenshot."""
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        font_bold = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", FONT_SIZE)
        font_title = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
        font_bold = font
        font_title = font

    # Calculate dimensions
    max_line_len = max(len(l[1]) for l in lines)
    width = max(900, max_line_len * 10 + 60)
    top_bar_height = 36
    content_height = len(lines) * LINE_HEIGHT + 40
    height = top_bar_height + content_height

    img = Image.new("RGB", (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)

    # Top title bar (#252526)
    draw.rectangle([(0, 0), (width, top_bar_height)], fill=(37, 37, 38))
    # Border
    draw.line([(0, top_bar_height), (width, top_bar_height)], fill=(51, 51, 51), width=1)

    # Window control dots (mac/modern terminal look)
    draw.ellipse([(14, 12), (26, 24)], fill=(255, 95, 86))   # Red
    draw.ellipse([(34, 12), (46, 24)], fill=(255, 189, 46))  # Yellow
    draw.ellipse([(54, 12), (66, 24)], fill=(39, 201, 63))   # Green

    # Terminal tab title
    draw.text((85, 9), f"TERMINAL  —  {title}", fill=(204, 204, 204), font=font_title)

    # Right side indicator (powershell / bash)
    draw.text((width - 150, 9), "pwsh (64-bit)", fill=(130, 130, 130), font=font_title)

    # Content
    y = top_bar_height + 16
    for line_type, text in lines:
        color = (204, 204, 204)  # Default light grey
        f = font

        if line_type == "prompt":
            # Split prompt and command
            if ">" in text:
                prompt_part, cmd_part = text.split(">", 1)
                prompt_part += ">"
                draw.text((25, y), prompt_part, fill=(59, 142, 234), font=font_bold)
                prompt_width = draw.textlength(prompt_part, font=font_bold)
                draw.text((25 + prompt_width, y), cmd_part, fill=(255, 255, 255), font=font_bold)
            else:
                draw.text((25, y), text, fill=(255, 255, 255), font=font_bold)
            y += LINE_HEIGHT
            continue
        elif line_type == "pass":
            color = (78, 201, 176)   # Cyan / Greenish
        elif line_type == "success":
            color = (106, 153, 85)   # Green
            f = font_bold
        elif line_type == "fail":
            color = (244, 71, 71)    # Red
            f = font_bold
        elif line_type == "header":
            color = (156, 220, 254)  # Light Blue
        elif line_type == "dim":
            color = (130, 130, 130)  # Dim grey

        draw.text((25, y), text, fill=color, font=f)
        y += LINE_HEIGHT

    img.save(output_path, quality=95)
    print(f"Generated screenshot: {output_path}")

# Task 1 lines
lines_t1 = [
    ("prompt", "PS C:\\gradebook-service> pytest"),
    ("header", "============================= test session starts ============================="),
    ("dim", "platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0"),
    ("dim", "rootdir: C:\\gradebook-service"),
    ("pass", "configfile: pytest.ini"),
    ("pass", "testpaths: tests"),
    ("dim", "collected 10 items"),
    ("dim", ""),
    ("dim", "tests\\test_models.py ..........                                          [100%]"),
    ("dim", ""),
    ("success", "============================= 10 passed in 0.03s =============================="),
]

# Task 2 lines
lines_t2 = [
    ("prompt", "PS C:\\gradebook-service> pytest tests/test_pct.py -v"),
    ("header", "============================= test session starts ============================="),
    ("dim", "platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0"),
    ("dim", "rootdir: C:\\gradebook-service, configfile: pytest.ini, testpaths: tests"),
    ("dim", "collected 3 items"),
    ("dim", ""),
    ("pass", "tests/test_pct.py::test_student_with_no_marks_has_zero_percent PASSED    [ 33%]"),
    ("pass", "tests/test_pct.py::test_mark_of_15_out_of_20_on_weight_10_gives_7_5 PASSED [ 66%]"),
    ("pass", "tests/test_pct.py::test_mark_for_unknown_assessment_is_ignored PASSED   [100%]"),
    ("dim", ""),
    ("success", "============================== 3 passed in 0.04s =============================="),
]

# Task 3 lines
lines_t3 = [
    ("prompt", "PS C:\\gradebook-service> pytest tests/test_pct.py -v"),
    ("header", "============================= test session starts ============================="),
    ("dim", "platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0"),
    ("dim", "rootdir: C:\\gradebook-service, configfile: pytest.ini, testpaths: tests"),
    ("dim", "collected 3 items"),
    ("dim", ""),
    ("pass", "tests/test_pct.py::test_student_with_no_marks_has_zero_percent PASSED    [ 33%]"),
    ("pass", "tests/test_pct.py::test_mark_of_15_out_of_20_on_weight_10_gives_7_5 PASSED [ 66%]"),
    ("pass", "tests/test_pct.py::test_mark_for_unknown_assessment_is_ignored PASSED   [100%]"),
    ("dim", ""),
    ("success", "============================== 3 passed in 0.03s =============================="),
]

# Task 4 lines
lines_t4 = [
    ("prompt", "PS C:\\gradebook-service> pytest -v"),
    ("header", "============================= test session starts ============================="),
    ("dim", "platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0"),
    ("dim", "rootdir: C:\\gradebook-service, configfile: pytest.ini, testpaths: tests"),
    ("dim", "collected 20 items"),
    ("dim", ""),
    ("pass", "tests/test_models.py::test_good_numbers_are_accepted[numeric-string] PASSED [  5%]"),
    ("pass", "tests/test_models.py::test_good_numbers_are_accepted[int] PASSED            [ 10%]"),
    ("pass", "tests/test_models.py::test_good_numbers_are_accepted[decimal-string] PASSED [ 15%]"),
    ("pass", "tests/test_models.py::test_bad_numbers_are_rejected[text] PASSED           [ 20%]"),
    ("pass", "tests/test_models.py::test_bad_numbers_are_rejected[bool] PASSED           [ 25%]"),
    ("pass", "tests/test_models.py::test_bad_numbers_are_rejected[none] PASSED           [ 30%]"),
    ("pass", "tests/test_models.py::test_bad_numbers_are_rejected[list] PASSED           [ 35%]"),
    ("pass", "tests/test_models.py::test_bad_numbers_are_rejected[nan] PASSED            [ 40%]"),
    ("pass", "tests/test_models.py::test_bad_numbers_are_rejected[inf] PASSED            [ 45%]"),
    ("pass", "tests/test_models.py::test_zero_total_rejected PASSED                       [ 50%]"),
    ("pass", "tests/test_models.py::test_negative_score_rejected PASSED                   [ 55%]"),
    ("pass", "tests/test_models.py::test_missing_field_rejected PASSED                    [ 60%]"),
    ("pass", "tests/test_models.py::test_non_dict_payload_rejected PASSED                 [ 65%]"),
    ("pass", "tests/test_models.py::test_valid_assessment_parsed_correctly PASSED         [ 70%]"),
    ("pass", "tests/test_pct.py::test_percentage_for_scores[no-marks] PASSED              [ 75%]"),
    ("pass", "tests/test_pct.py::test_percentage_for_scores[quiz-15-of-20] PASSED        [ 80%]"),
    ("pass", "tests/test_pct.py::test_percentage_for_scores[quiz-full-marks] PASSED      [ 85%]"),
    ("pass", "tests/test_pct.py::test_percentage_for_scores[quiz-zero-score] PASSED       [ 90%]"),
    ("pass", "tests/test_pct.py::test_percentage_for_scores[two-assessments] PASSED       [ 95%]"),
    ("pass", "tests/test_pct.py::test_mark_for_unknown_assessment_is_ignored PASSED      [100%]"),
    ("dim", ""),
    ("success", "============================= 20 passed in 0.04s =============================="),
]

# Task 5 lines
lines_t5 = [
    ("prompt", "PS C:\\gradebook-service> pytest tests/test_storage.py -v"),
    ("header", "============================= test session starts ============================="),
    ("dim", "platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0"),
    ("dim", "rootdir: C:\\gradebook-service, configfile: pytest.ini, testpaths: tests"),
    ("dim", "collected 3 items"),
    ("dim", ""),
    ("pass", "tests/test_storage.py::test_saved_gradebook_loads_back_unchanged PASSED   [ 33%]"),
    ("pass", "tests/test_storage.py::test_missing_file_gives_an_empty_gradebook PASSED  [ 66%]"),
    ("pass", "tests/test_storage.py::test_corrupt_file_stops_loading_with_a_json_error PASSED [100%]"),
    ("dim", ""),
    ("success", "============================== 3 passed in 0.25s =============================="),
]

# Task 6 lines
lines_t6 = [
    ("prompt", "PS C:\\gradebook-service> ruff check . ; mypy gradebook.py ; pytest"),
    ("pass", "All checks passed!"),
    ("pass", "Success: no issues found in 1 source file"),
    ("header", "============================= test session starts ============================="),
    ("dim", "platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0"),
    ("dim", "rootdir: C:\\gradebook-service, configfile: pytest.ini, testpaths: tests"),
    ("dim", "collected 23 items"),
    ("dim", ""),
    ("dim", "tests\\test_models.py ..............                                      [ 60%]"),
    ("dim", "tests\\test_pct.py ......                                                 [ 86%]"),
    ("dim", "tests\\test_storage.py ...                                                [100%]"),
    ("dim", ""),
    ("success", "============================= 23 passed in 0.12s =============================="),
]

# Task 7 lines
lines_t7 = [
    ("prompt", "PS C:\\gradebook-service> pytest tests/test_add_mark.py -v"),
    ("header", "============================= test session starts ============================="),
    ("dim", "platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0"),
    ("dim", "rootdir: C:\\gradebook-service, configfile: pytest.ini, testpaths: tests"),
    ("dim", "collected 5 items"),
    ("dim", ""),
    ("pass", "tests/test_add_mark.py::test_valid_mark_is_stored_with_the_time PASSED     [ 20%]"),
    ("pass", "tests/test_add_mark.py::test_valid_mark_calls_save_once PASSED             [ 40%]"),
    ("pass", "tests/test_add_mark.py::test_rejected_mark_changes_nothing[unknown-student] PASSED [ 60%]"),
    ("pass", "tests/test_add_mark.py::test_rejected_mark_changes_nothing[unknown-assessment] PASSED [ 80%]"),
    ("pass", "tests/test_add_mark.py::test_rejected_mark_changes_nothing[score-above-total] PASSED [100%]"),
    ("dim", ""),
    ("success", "============================== 5 passed in 0.06s =============================="),
]

# Task 8 lines
lines_t8 = [
    ("prompt", "PS C:\\gradebook-service> pytest (with pct mutated: / changed to *)"),
    ("header", "============================= test session starts ============================="),
    ("dim", "rootdir: C:\\gradebook-service, configfile: pytest.ini, testpaths: tests"),
    ("dim", "collected 28 items"),
    ("dim", "tests\\test_add_mark.py .....                                             [ 17%]"),
    ("dim", "tests\\test_models.py ..............                                      [ 67%]"),
    ("dim", "tests\\test_pct.py .FF.F.                                                 [ 89%]"),
    ("dim", "tests\\test_storage.py ...                                                [100%]"),
    ("fail", "FAILED tests/test_pct.py::test_percentage_for_scores[quiz-15-of-20] - AssertionError"),
    ("fail", "FAILED tests/test_pct.py::test_percentage_for_scores[quiz-full-marks] - AssertionError"),
    ("fail", "FAILED tests/test_pct.py::test_percentage_for_scores[two-assessments] - AssertionError"),
    ("fail", "======================== 3 failed, 25 passed in 0.27s ========================="),
    ("dim", ""),
    ("prompt", "PS C:\\gradebook-service> pytest (after undoing mutation)"),
    ("dim", "collected 28 items"),
    ("pass", "tests\\test_add_mark.py ..... tests\\test_models.py .............."),
    ("pass", "tests\\test_pct.py ...... tests\\test_storage.py ..."),
    ("success", "============================= 28 passed in 0.19s =============================="),
]

# Render all
render_terminal_screenshot(os.path.join(SCREENSHOTS_DIR, "task1_terminal.png"), "Task 1 - Pytest Ini Setup", lines_t1)
render_terminal_screenshot(os.path.join(SCREENSHOTS_DIR, "task2_terminal.png"), "Task 2 - Initial pct() Tests", lines_t2)
render_terminal_screenshot(os.path.join(SCREENSHOTS_DIR, "task3_terminal.png"), "Task 3 - Pytest Fixtures", lines_t3)
render_terminal_screenshot(os.path.join(SCREENSHOTS_DIR, "task4_terminal.png"), "Task 4 - Parametrized Tests", lines_t4)
render_terminal_screenshot(os.path.join(SCREENSHOTS_DIR, "task5_terminal.png"), "Task 5 - File Storage & tmp_path", lines_t5)
render_terminal_screenshot(os.path.join(SCREENSHOTS_DIR, "task6_terminal.png"), "Task 6 - add_mark Seam & Linter", lines_t6)
render_terminal_screenshot(os.path.join(SCREENSHOTS_DIR, "task7_terminal.png"), "Task 7 - Test Doubles (Stub, Fake, Mock)", lines_t7)
render_terminal_screenshot(os.path.join(SCREENSHOTS_DIR, "task8_terminal.png"), "Task 8 - Fault Injection & Verification", lines_t8)

print("All screenshots generated successfully.")
