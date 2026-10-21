"""Build a source-only upload archive from an explicit allowlist."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = [
    ".gitignore", ".github/workflows/ci.yml", "LICENSE", "README.md", "README.zh-CN.md",
    "THIRD_PARTY_NOTICES.md", "CONTRIBUTING.md", "pyproject.toml",
    "docs/data-format.md", "docs/model-card.md", "docs/release.md", "docs/verification.md",
    "examples/synthetic.json", "src/fish_length/__init__.py",
    "src/fish_length/measurement.py", "src/fish_length/inference.py",
    "src/fish_length/cli.py", "src/fish_length/zed.py",
    "tests/test_measurement.py", "tests/test_cli.py", "tools/build_public_bundle.py",
]


def build():
    for name in PUBLIC_FILES:
        if not (ROOT / name).is_file():
            raise FileNotFoundError(name)
    output = ROOT / "dist/fish-length-estimation-0.1.0-source.zip"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name in PUBLIC_FILES:
            archive.write(ROOT / name, f"fish-length-estimation/{name}")
    print(output)
    return output


if __name__ == "__main__":
    build()
