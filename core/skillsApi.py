import json
import re
import zipfile
import io
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = BASE_DIR / "skills"
SKILLS_FILE = BASE_DIR / "skills.json"

router = APIRouter(prefix="/api")

SKILLS_DIR.mkdir(exist_ok=True)
if not SKILLS_FILE.exists():
    SKILLS_FILE.write_text("[]", encoding="utf-8")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9а-яё_-]+", "-", value, flags=re.I)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "skill"


def unique_filename(filename):
    filename = str(filename or "skill.md")
    stem = Path(filename).stem
    ext = Path(filename).suffix or ".md"
    base = f"{slugify(stem)}{ext}"
    path = SKILLS_DIR / base
    if not path.exists():
        return base
    i = 2
    while True:
        candidate = f"{slugify(stem)}-{i}{ext}"
        if not (SKILLS_DIR / candidate).exists():
            return candidate
        i += 1


def load_skills():
    try:
        data = json.loads(SKILLS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except Exception:
        pass
    return []


def save_skills(skills):
    SKILLS_FILE.write_text(json.dumps(skills, ensure_ascii=False, indent=2), encoding="utf-8")


def first_line(text):
    for line in str(text or "").splitlines():
        line = line.strip()
        if line:
            return line[:240]
    return ""


def extract_tags(text):
    tags = []
    for line in str(text or "").splitlines():
        m = re.match(r"^\s*tags?\s*:\s*(.+)$", line, re.I)
        if m:
            tags = [x.strip() for x in re.split(r"[,;]", m.group(1)) if x.strip()]
            break
    return tags


def skill_keys(skill):
    keys = set()
    name = slugify(skill.get("name", ""))
    if name:
        keys.add(name)
    filename = skill.get("filename", "")
    if filename:
        keys.add(slugify(Path(filename).stem))
    return keys


def same_skill(a, b):
    return bool(skill_keys(a) & skill_keys(b))


def write_skill_file(filename, content):
    path = SKILLS_DIR / filename
    path.write_text(str(content or ""), encoding="utf-8")
    return path


def save_skill_payload(data, source="manual", filename=None):
    name = str(data.get("name") or "").strip()
    content = str(data.get("content") or "").strip()
    if not content:
        return None, "Skill content required"
    if not name:
        name = Path(filename).stem if filename else f"Навык {len(load_skills()) + 1}"
    if not filename:
        filename = unique_filename(f"{slugify(name)}.md")
    record = {
        "name": name,
        "filename": filename,
        "content": content,
        "description": str(data.get("description") or first_line(content)),
        "tags": data.get("tags") if isinstance(data.get("tags"), list) else extract_tags(content),
        "source": source,
        "created_at": data.get("created_at") or now_iso(),
        "updated_at": now_iso(),
    }
    write_skill_file(filename, content)
    skills = load_skills()
    replaced = False
    for i, skill in enumerate(skills):
        if same_skill(skill, record):
            record["created_at"] = skill.get("created_at", record["created_at"])
            skills[i] = record
            replaced = True
            break
    if not replaced:
        skills.append(record)
    save_skills(skills)
    return record, None


def delete_skill_by_id(skill_id):
    skill_id = slugify(Path(skill_id).stem) if "." in skill_id else slugify(skill_id)
    skills = load_skills()
    kept = []
    removed = None
    for skill in skills:
        keys = skill_keys(skill)
        if skill_id in keys:
            removed = skill
        else:
            kept.append(skill)
    if not removed:
        return None
    save_skills(kept)
    filename = removed.get("filename")
    if filename:
        path = SKILLS_DIR / filename
        if path.exists():
            path.unlink()
    return removed


def tokens(text):
    return set(x.lower() for x in re.findall(r"[0-9A-Za-zА-Яа-я_]+", str(text or "")))


def score_skill(query, skill):
    q = tokens(query)
    if not q:
        return 0
    name = str(skill.get("name", ""))
    desc = str(skill.get("description", ""))
    content = str(skill.get("content", ""))[:4000]
    tags = skill.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    s = tokens(" ".join([name, desc, content, " ".join(tags)]))
    score = len(q & s)
    if name and name.lower() in str(query).lower():
        score += 5
    for tag in tags:
        if str(tag).lower() in str(query).lower():
            score += 2
    return score


def select_relevant_skills(query, skills, limit=3):
    ranked = []
    for skill in skills:
        sc = score_skill(query, skill)
        if sc > 0:
            ranked.append((sc, skill))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [skill for _, skill in ranked[:limit]]


@router.get("/skills")
async def get_skills():
    return JSONResponse(content=load_skills())


@router.post("/skills")
async def add_skill(request: dict):
    skill, err = save_skill_payload(request, source="manual")
    if err:
        return JSONResponse(content={"status": "error", "message": err}, status_code=400)
    return JSONResponse(content={"status": "success", "message": "Skill saved", "skill": skill})


@router.post("/skills/upload-zip")
async def upload_zip_skills(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            md_files = []
            for name in zf.namelist():
                if name.endswith(".md"):
                    try:
                        content = zf.read(name).decode("utf-8", errors="ignore").strip()
                        if content:
                            md_files.append((Path(name).stem, content))
                    except Exception:
                        pass

            if not md_files:
                return JSONResponse(
                    content={"status": "error", "message": "No .md files found in ZIP"},
                    status_code=400,
                )

            uploaded_skills = []
            for stem, content in md_files:
                filename = unique_filename(f"{slugify(stem)}.md")
                skill, err = save_skill_payload(
                    {
                        "name": stem,
                        "content": content,
                        "description": first_line(content),
                        "tags": extract_tags(content),
                    },
                    source="zip",
                    filename=filename,
                )
                if not err:
                    uploaded_skills.append(skill)

            if not uploaded_skills:
                return JSONResponse(
                    content={"status": "error", "message": "Failed to process .md files"},
                    status_code=400,
                )

            return JSONResponse(
                content={
                    "status": "success",
                    "message": f"Loaded {len(uploaded_skills)} skills from ZIP",
                    "skills": uploaded_skills,
                }
            )
    except zipfile.BadZipFile:
        return JSONResponse(
            content={"status": "error", "message": "Invalid ZIP file"}, status_code=400
        )
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.post("/skills/upload")
async def upload_skill(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        text = raw.decode("utf-8", errors="ignore").strip()
    except Exception:
        text = ""
    if not text:
        return JSONResponse(
            content={"status": "error", "message": "Empty file"}, status_code=400
        )
    original = file.filename or "skill.md"
    filename = unique_filename(original)
    skill, err = save_skill_payload(
        {
            "name": Path(original).stem,
            "content": text,
            "description": first_line(text),
            "tags": extract_tags(text),
        },
        source="upload",
        filename=filename,
    )
    if err:
        return JSONResponse(content={"status": "error", "message": err}, status_code=400)
    return JSONResponse(content={"status": "success", "message": "Uploaded", "skill": skill})


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    removed = delete_skill_by_id(skill_id)
    if not removed:
        return JSONResponse(
            content={"status": "error", "message": "Skill not found"}, status_code=404
        )
    return JSONResponse(content={"status": "success", "message": "Skill deleted"})


@router.post("/train")
async def train_skill(request: dict):
    skill, err = save_skill_payload(request, source="manual")
    if err:
        return JSONResponse(content={"status": "error", "message": err}, status_code=400)
    return JSONResponse(
        content={"status": "success", "message": "Skill saved", "trained": False, "skill": skill}
    )
