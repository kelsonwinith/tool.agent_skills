#!/usr/bin/env python3
"""Scaffold a feature module following the layered React architecture.

Creates, under <root>/features/<feature>/:
  <feature>.feature.ts                                  public feature entrypoint
  components/<component>/<component>.component.tsx      pure view (zero className)
  components/<component>/<component>.hook.ts            state, hooks, handlers
  components/<component>/<component>.type.ts            Props and component types

Names are normalized to camelCase (files/exports) and PascalCase (components).
The generated files are stubs with TODO markers — fill them in, don't ship them as-is.

Usage:
    python scripts/new_feature.py <feature> [--component NAME] [--root DIR]
    python scripts/new_feature.py userProfile
    python scripts/new_feature.py billing --component invoiceList --root ./src
"""

import argparse
import re
import sys
from pathlib import Path


def to_camel(name: str) -> str:
    parts = [p for p in re.split(r"[-_\s]+", name.strip()) if p]
    if not parts:
        return ""
    return parts[0][:1].lower() + parts[0][1:] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def to_pascal(name: str) -> str:
    return to_camel(name)[:1].upper() + to_camel(name)[1:]


COMPONENT_TEMPLATE = '''"use client";

import type {{ {pascal}Props }} from "./{comp}.type";
import {{ use{pascal} }} from "./{comp}.hook";

export default function {pascal}(props: {pascal}Props) {{
  const {{ /* resolved values */ }} = use{pascal}(props);

  return (
    <>
      {{/* TODO: compose UI primitives (/components) and layouts (/layouts). No inline styling here. */}}
    </>
  );
}}
'''

HOOK_TEMPLATE = '''import type {{ {pascal}Props }} from "./{comp}.type";

/**
 * Resolves {comp} props into the values the view renders.
 *
 * return: the values the view needs; never returns undefined.
 */
export function use{pascal}(props: {pascal}Props) {{
  // TODO: add state, store selectors, and handlers; resolve optional props to concrete values.
  return {{ ...props }};
}}
'''

TYPE_TEMPLATE = '''export interface {pascal}Props {{
  // TODO: add props. Optional (`?`) is allowed here and only here; the hook resolves defaults.
}}
'''

FEATURE_TEMPLATE = '''export {{ default as {pascal} }} from "./components/{comp}/{comp}.component";
// TODO: re-export other public pieces of this feature (hooks, types, services).
'''


def scaffold(feature: str, component: str, root: Path):
    feature_camel = to_camel(feature)
    comp_camel = to_camel(component)
    pascal = to_pascal(component)

    feature_dir = root / "features" / feature_camel
    component_dir = feature_dir / "components" / comp_camel

    files = {
        feature_dir / f"{feature_camel}.feature.ts": FEATURE_TEMPLATE.format(pascal=pascal, comp=comp_camel),
        component_dir / f"{comp_camel}.component.tsx": COMPONENT_TEMPLATE.format(pascal=pascal, comp=comp_camel),
        component_dir / f"{comp_camel}.hook.ts": HOOK_TEMPLATE.format(pascal=pascal, comp=comp_camel),
        component_dir / f"{comp_camel}.type.ts": TYPE_TEMPLATE.format(pascal=pascal),
    }

    created = []
    skipped = []
    for path, content in files.items():
        if path.exists():
            skipped.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(path)
    return created, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("feature", help="feature name, e.g. userProfile or user-profile")
    parser.add_argument("--component", default=None, help="main component name (default: the feature name)")
    parser.add_argument("--root", default=".", help="project root that contains features/ (default: .)")
    args = parser.parse_args()

    component = args.component or args.feature
    if not to_camel(args.feature):
        print("FAIL  feature name must contain at least one letter or digit", file=sys.stderr)
        return 1

    created, skipped = scaffold(args.feature, component, Path(args.root))

    for path in created:
        print(f"CREATE  {path}")
    for path in skipped:
        print(f"SKIP    {path} (already exists)")

    if not created:
        print("\nNothing to do.")
        return 0
    print(f"\nScaffolded feature '{to_camel(args.feature)}' with component '{to_camel(component)}'.")
    print("Next: fill the TODO stubs, place shared visuals in /components and /layouts, and add a service if needed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
