"""Score every submission in submissions/ and produce a scorecard.

Put each CVAT export at  submissions/<task_name>.zip  (or a folder of that name),
e.g. submissions/easy_semantic.zip, submissions/medium_instance.zip,
submissions/cp1_holes.zip ...

Usage:  python scoring/scorecard.py [--dir submissions] [--out reports]
        python scoring/scorecard.py --group tiers --out reports/tiers

Writes SCORECARD.md and scorecard.json under --out only when every submitted
task in the selected group can be evaluated against its reference. All tasks
sum to 100; the three tiers alone sum to 82.
Review signals are not evidence of misconduct.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import lab_utils as L  # noqa: E402
from scoring.score import load_registry, resolve_task, require_reference, _guard_match  # noqa: E402


def score_one(name, sub_path, reg=None):
    reg = reg or load_registry()
    info, base, classes = resolve_task(reg, name)
    ttype = info["type"]
    require_reference(base, ttype)
    _guard_match(reg, name, base, ttype, sub_path)
    gt_dir = base / "groundtruth"
    cap, floor = L.HUMAN_CAP, L.FLOOR
    if ttype == "semantic":
        name2id = classes["trainid"]
        id2name = {v: k for k, v in name2id.items()}
        sub = L.load_semantic_submission(sub_path, name2id)
        gt = L.load_semantic_gt(gt_dir, set(name2id.values()))
        result = L.score_semantic(sub, gt, id2name)
    elif ttype == "panoptic":
        cap, floor = L.PQ_CAP, L.PQ_FLOOR
        cn = set(classes["classes"]); stuff = set(classes["stuff"])
        catid2name = {int(k): v for k, v in classes["catid2name"].items()}
        pred = L.build_pred_panoptic(L._find_coco_json(L._read_members(sub_path)), cn, stuff)
        gt = L.load_panoptic_gt(gt_dir / "panoptic.json", gt_dir / "png", catid2name, cn)
        result = L.score_panoptic(pred, gt, cn)
    else:
        members = L._read_members(sub_path)
        gt_coco = json.load(open(gt_dir / "instances.json"))
        result = L.score_instance(L._find_coco_json(members), gt_coco, set(classes["classes"]))
    pts = L.metric_to_points(result["value"], info.get("weight", 0), cap=cap, floor=floor)
    return dict(type=ttype, group=info["_group"], weight=info.get("weight", 0), points=pts,
                value=round(result["value"], 3), flags=L.cheat_flags(ttype, result))


def find_submission(sub_dir, name):
    for cand in (sub_dir / f"{name}.zip", sub_dir / name):
        if cand.exists():
            return cand
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="submissions")
    ap.add_argument("--out", default="reports")
    ap.add_argument("--group", choices=("all", "tiers", "checkpoints"), default="all",
                    help="score only one task group when only its references are available")
    args = ap.parse_args()
    sub_dir = ROOT / args.dir
    reg = load_registry()

    # tiers first, then checkpoints — every task counts toward the 100
    order = ([n for n, i in reg.items() if i["_group"] == "tiers"]
             + [n for n, i in reg.items() if i["_group"] == "checkpoints"])
    if args.group != "all":
        order = [n for n in order if reg[n]["_group"] == args.group]

    submissions = {name: find_submission(sub_dir, name) for name in order}
    if not any(submissions.values()):
        ap.error(f"No task exports found in {sub_dir}; no scorecard was written")
    for name, sub in submissions.items():
        if sub:
            info, base, _ = resolve_task(reg, name)
            try:
                require_reference(base, info["type"])
                _guard_match(reg, name, base, info["type"], sub)
            except (ValueError, FileNotFoundError) as exc:
                ap.error(f"Cannot score {name}: {exc}; no scorecard was written")

    rows, all_flags = {}, []
    total = 0.0
    for name in order:
        sub = submissions[name]
        if not sub:
            rows[name] = {"type": reg[name]["type"], "group": reg[name]["_group"],
                          "points": 0.0, "weight": reg[name].get("weight", 0),
                          "value": None, "flags": [], "missing": True}
            continue
        try:
            r = score_one(name, sub, reg)
        except (ValueError, FileNotFoundError, KeyError, OSError) as exc:
            ap.error(f"Cannot score {name}: {exc}; no scorecard was written")
        rows[name] = r
        total += r["points"]
        for f in r["flags"]:
            all_flags.append(f"[{name}] {f}")

    total = round(total, 1)
    max_total = sum(reg[name].get("weight", 0) for name in order)
    out = {"total": total, "max": max_total, "group": args.group,
           "review_flags": all_flags, "tasks": rows}
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "scorecard.json").write_text(json.dumps(out, indent=2))

    lines = ["# Day-5 Segmentation — Scorecard", ""]
    if all_flags:
        lines += ["> ⚠️ **Review signals — human interpretation required:**"]
        lines += [f"> - {f}" for f in all_flags] + [""]
    lines += [f"**Total: {total} / {max_total}**", "",
              "| Task | Group | Type | Metric | Points |", "| --- | --- | --- | ---: | ---: |"]
    for name in order:
        r = rows[name]
        val = "—" if r.get("value") is None else f"{r['value']:.3f}"
        note = " (missing)" if r.get("missing") else (" (error)" if r.get("error") else "")
        lines.append(f"| {name}{note} | {r.get('group','?')} | {r.get('type','?')} | {val} "
                     f"| {r['points']} / {r['weight']} |")
    (outdir / "SCORECARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwrote {outdir/'SCORECARD.md'} and scorecard.json")


if __name__ == "__main__":
    main()
