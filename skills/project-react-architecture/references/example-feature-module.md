# Example Feature Module

A complete, small feature module. Use it as a target shape for what `scripts/new_feature.py` scaffolds and what you fill in.

```text
features/userProfile/
├── userProfile.feature.ts                 # public entrypoint (named exports only)
├── components/
│   └── userCard/
│       ├── userCard.component.tsx         # pure view — zero className
│       ├── userCard.hook.ts               # state, handlers, resolved props
│       ├── userCard.type.ts               # Props & component types
│       ├── userCard.service.ts            # network calls → RequestState<T>
│       └── userCard.constant.ts           # labels / static config
└── types/
    └── user.type.ts                       # feature domain type
```

## Key files

### `userCard.component.tsx`

```tsx
"use client";

import type { UserCardProps } from "./userCard.type";
import { useUserCard } from "./userCard.hook";
import CardLayout from "@/layouts/card/cardLayout.layout";
import DimmedText from "@/components/text/dimmedText.ui";
import ParagraphText from "@/components/text/paragraphText.ui";
import DeleteButton from "@/components/button/deleteButton.ui";

export default function UserCard(props: UserCardProps) {
  const { user, isDeleting, handleDelete } = useUserCard(props);

  return (
    <CardLayout>
      <DimmedText>{user.role}</DimmedText>
      <ParagraphText bold>{user.name}</ParagraphText>
      <DeleteButton isBusy={isDeleting} onDelete={handleDelete}>
        Delete
      </DeleteButton>
    </CardLayout>
  );
}
```

### `userCard.hook.ts`

```ts
import type { UserCardProps } from "./userCard.type";
import { useUserCardStore } from "../userCard.store";

/**
 * Resolves the user card props into view values and handlers.
 *
 * return: the values the view renders; never returns undefined.
 */
export function useUserCard({ user, onDeleted }: UserCardProps) {
  const { status, remove } = useUserCardStore();

  async function handleDelete() {
    const ok = await remove(user.id);
    if (ok) onDeleted?.(user.id);
  }

  return { user, isDeleting: status === "loading", handleDelete };
}
```

### `userCard.type.ts`

```ts
import type { User } from "../../types/user.type";

export interface UserCardProps {
  user: User;
  onDeleted?: (userId: string) => void;
}
```

### `userCard.service.ts`

```ts
import type { RequestState } from "../../types/requestState.type";

/** Deletes a user, mapping failures into the RequestState contract. */
export async function deleteUserRequest(userId: string): Promise<RequestState<null>> {
  try {
    const response = await fetch(`/api/users/${userId}`, { method: "DELETE" });
    if (!response.ok) return { status: "error", data: null, error: `HTTP ${response.status}` };
    return { status: "success", data: null, error: null };
  } catch (error) {
    return { status: "error", data: null, error: String(error) };
  }
}
```

### `userProfile.feature.ts`

```ts
export { default as UserCard } from "./components/userCard/userCard.component";
export type { User } from "./types/user.type";
```

Note how the view owns no styling and no data fetching, the hook owns behavior, the service owns the network boundary, and every shared visual piece lives in `/components` or `/layouts`.
