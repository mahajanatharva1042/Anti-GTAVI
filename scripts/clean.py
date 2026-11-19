"""Clean up intermediate files and clips used to create final videos.

Reclaims disk space by deleting large source videos, temporary audio waveforms,
intermediate subtitle files, and unwanted test cuts in edits/ once final videos are produced.

usage:
  python scripts/clean.py jobs/<id>                   # Clean intermediate files (source.mp4, audio.wav, .ass)
  python scripts/clean.py jobs/<id> --keep-pick 4     # Keep only clip_4 in edits/, delete other candidate clips
  python scripts/clean.py jobs/<id> --edits           # Also delete final clips in edits/ (e.g. after uploading)
  python scripts/clean.py --all                       # Clean intermediate files across all jobs
  python scripts/clean.py --dry-run                   # Preview files to delete and reclaimed space
"""
import argparse, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import JOBS, ROOT


def format_bytes(n):
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    elif n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    else:
        return f"{n / (1024 * 1024 * 1024):.2f} GB"


def clean_job(job_dir, keep_pick=None, clean_edits=False, only_edits=False, dry_run=False):
    job = Path(job_dir).resolve()
    if not job.is_dir():
        print(f"Skipping: {job} is not a directory")
        return 0, 0

    to_delete = []

    if not only_edits:
        # 1. Intermediate source video files that were required to cut final video
        for p in job.glob("source*"):
            if p.is_file():
                to_delete.append(p)

        # 2. Intermediate 16kHz audio waveform used for Whisper / loudness analysis
        audio = job / "audio.wav"
        if audio.is_file():
            to_delete.append(audio)

    # 3. Intermediate ASS subtitle files in edits/
    edits = job / "edits"
    if edits.is_dir():
        for p in edits.glob("*.ass"):
            if p.is_file():
                to_delete.append(p)

        # 4. If keep_pick specified, delete other candidate cuts in edits/
        if keep_pick is not None:
            for p in edits.glob("clip_*"):
                name = p.stem  # e.g. clip_1
                if name.startswith("clip_"):
                    try:
                        num = int(name.split("_")[1])
                        if num != keep_pick:
                            to_delete.append(p)
                    except (ValueError, IndexError):
                        pass

        # 5. If clean_edits or only_edits is True (user explicitly wants to purge edits/ folder after uploading)
        if clean_edits or only_edits:
            for p in edits.glob("*"):
                if p.is_file():
                    to_delete.append(p)

    # Deduplicate list
    to_delete = list(dict.fromkeys(to_delete))

    freed = 0
    deleted_count = 0

    print(f"\nCleaning job: {job.name}")
    if not to_delete:
        print("  No intermediate or unneeded files found.")
        return 0, 0

    for f in to_delete:
        try:
            sz = f.stat().st_size
            if not dry_run:
                f.unlink(missing_ok=True)
                print(f"  Deleted: {f.name} ({format_bytes(sz)})")
            else:
                print(f"  [Dry-run] Would delete: {f.name} ({format_bytes(sz)})")
            freed += sz
            deleted_count += 1
        except Exception as e:
            print(f"  Error deleting {f.name}: {e}")

    # Remove edits dir if empty
    if not dry_run and edits.is_dir():
        try:
            if not any(edits.iterdir()):
                edits.rmdir()
        except Exception:
            pass

    return deleted_count, freed


def main():
    ap = argparse.ArgumentParser(description="Clean up intermediate files and clips used to create final videos.")
    ap.add_argument("job", nargs="?", default=None, help="Job directory to clean (e.g. jobs/<id>)")
    ap.add_argument("--all", action="store_true", help="Clean intermediate files across all jobs in jobs/")
    ap.add_argument("--keep-pick", type=int, default=None, help="In edits/, keep only this clip pick and delete others")
    ap.add_argument("--edits", action="store_true", help="Delete all clips in edits/ folder (e.g. after uploading)")
    ap.add_argument("--only-edits", action="store_true", help="Delete only the clips in edits/ folder, keeping raw sources")
    ap.add_argument("--dry-run", action="store_true", help="Preview files to delete without actually deleting")
    args = ap.parse_args()

    if not args.job and not args.all:
        # Default: if jobs exists, check if there's only one job or show usage
        if JOBS.is_dir():
            subdirs = [p for p in JOBS.iterdir() if p.is_dir()]
            if len(subdirs) == 1:
                args.job = str(subdirs[0])
            elif len(subdirs) > 1:
                ap.print_help()
                print("\nAvailable jobs:")
                for p in subdirs:
                    print(f"  jobs/{p.name}")
                sys.exit(0)
            else:
                sys.exit("No jobs found in jobs/")
        else:
            sys.exit("No jobs/ folder found.")

    total_count = 0
    total_freed = 0

    if args.all:
        if not JOBS.is_dir():
            sys.exit("No jobs/ directory found.")
        for p in JOBS.iterdir():
            if p.is_dir():
                c, f = clean_job(p, keep_pick=args.keep_pick, clean_edits=args.edits, only_edits=args.only_edits, dry_run=args.dry_run)
                total_count += c
                total_freed += f
    else:
        c, f = clean_job(args.job, keep_pick=args.keep_pick, clean_edits=args.edits, only_edits=args.only_edits, dry_run=args.dry_run)
        total_count += c
        total_freed += f

    action_label = "Would reclaim" if args.dry_run else "Reclaimed"
    print(f"\n{action_label} {format_bytes(total_freed)} across {total_count} file(s).")


if __name__ == "__main__":
    main()
