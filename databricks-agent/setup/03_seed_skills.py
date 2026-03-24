# ============================================================
# FILE: setup/03_seed_skills.py
# Uploads local skill files to the Unity Catalog Volume and
# writes _index.json so the agent can discover all skills.
#
# Run this as a Databricks notebook (attach to any cluster
# with Unity Catalog access) or via databricks-connect.
# ============================================================
# Databricks notebook source

# COMMAND ----------
import json
import os
import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VOLUME_PATH   = "/Volumes/ai_agent/skills/library"
LOCAL_SKILLS  = "./skills"   # relative to repo root when cloned on DBFS / Repos

# ---------------------------------------------------------------------------
# Helper: recursively list local skill directories
# ---------------------------------------------------------------------------
def discover_local_skills(base_path: str) -> list[dict]:
    """
    Walk the local skills/ directory and return a list of skill metadata
    dicts parsed from the YAML front-matter inside each SKILL.md.
    """
    import re
    skills = []

    if not os.path.isdir(base_path):
        print(f"[WARN] Local skills directory not found: {base_path}")
        return skills

    for skill_name in os.listdir(base_path):
        skill_dir = os.path.join(base_path, skill_name)
        skill_md  = os.path.join(skill_dir, "SKILL.md")

        if not os.path.isfile(skill_md):
            continue

        with open(skill_md, "r", encoding="utf-8") as f:
            raw = f.read()

        # Parse YAML front-matter between --- delimiters
        meta = {"name": skill_name, "description": "", "keywords": []}
        fm_match = re.match(r"^---\s*\n(.*?)\n---", raw, re.DOTALL)
        if fm_match:
            for line in fm_match.group(1).splitlines():
                line = line.strip()
                if line.startswith("name:"):
                    meta["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    meta["description"] = line.split(":", 1)[1].strip()
                elif line.startswith("keywords:"):
                    kw_raw = line.split(":", 1)[1].strip()
                    # Support both inline list "kw1, kw2" and YAML list items
                    meta["keywords"] = [k.strip().lstrip("- ") for k in kw_raw.split(",") if k.strip()]

        meta["skill_dir"]  = skill_name
        meta["indexed_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        skills.append(meta)

    return skills

# COMMAND ----------
# ---------------------------------------------------------------------------
# Step 1: Copy skill files into the Volume
# ---------------------------------------------------------------------------
print("=" * 60)
print("Step 1: Uploading skill files to Volume")
print("=" * 60)

skills_meta = discover_local_skills(LOCAL_SKILLS)

if not skills_meta:
    print("[WARN] No skills found in ./skills/. Ensure the repo is cloned correctly.")
else:
    for skill in skills_meta:
        skill_name = skill["skill_dir"]
        src = f"{LOCAL_SKILLS}/{skill_name}"
        dst = f"{VOLUME_PATH}/{skill_name}"

        print(f"  Uploading: {skill_name} -> {dst}")

        # Copy the SKILL.md
        skill_md_src = f"{src}/SKILL.md"
        skill_md_dst = f"{dst}/SKILL.md"
        try:
            dbutils.fs.cp(skill_md_src, skill_md_dst, recurse=False)
            print(f"    [OK] SKILL.md")
        except Exception as e:
            print(f"    [ERR] SKILL.md: {e}")

        # Copy references/ subdirectory if it exists
        refs_src = f"{src}/references"
        refs_dst = f"{dst}/references"
        try:
            files = dbutils.fs.ls(refs_src)
            for f in files:
                dbutils.fs.cp(f.path, f"{refs_dst}/{f.name}", recurse=False)
            print(f"    [OK] references/ ({len(files)} files)")
        except Exception:
            pass  # references/ is optional

        # Copy scripts/ subdirectory if it exists
        scripts_src = f"{src}/scripts"
        scripts_dst = f"{dst}/scripts"
        try:
            files = dbutils.fs.ls(scripts_src)
            for f in files:
                dbutils.fs.cp(f.path, f"{scripts_dst}/{f.name}", recurse=False)
            print(f"    [OK] scripts/ ({len(files)} files)")
        except Exception:
            pass  # scripts/ is optional

print(f"\nUploaded {len(skills_meta)} skill(s).")

# COMMAND ----------
# ---------------------------------------------------------------------------
# Step 2: Write _index.json
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("Step 2: Writing _index.json")
print("=" * 60)

index = {
    "version":    "1.0",
    "generated":  datetime.datetime.utcnow().isoformat() + "Z",
    "skills":     skills_meta,
}

index_json = json.dumps(index, indent=2, ensure_ascii=False)
index_path = f"{VOLUME_PATH}/_index.json"

# Write via dbutils (text file approach using sc)
index_path_dbfs = index_path  # Volumes are accessible as /Volumes/...

# Use Python open() which works in Databricks Volumes directly
with open(index_path, "w", encoding="utf-8") as f:
    f.write(index_json)

print(f"[OK] Written: {index_path}")
print(f"     Skills indexed: {len(skills_meta)}")
for s in skills_meta:
    print(f"       - {s['name']}: {s['description'][:60]}")

# COMMAND ----------
# ---------------------------------------------------------------------------
# Step 3: Verify
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("Step 3: Verification")
print("=" * 60)

try:
    volume_files = dbutils.fs.ls(VOLUME_PATH)
    print(f"Files in {VOLUME_PATH}:")
    for vf in volume_files:
        print(f"  {vf.path}  ({vf.size} bytes)")
except Exception as e:
    print(f"[ERR] Could not list volume: {e}")

print("\nDone. Skill seeding complete.")
