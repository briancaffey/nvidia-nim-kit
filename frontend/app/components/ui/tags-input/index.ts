import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as TagsInput } from "./TagsInput.vue"
export { default as TagsInputInput } from "./TagsInputInput.vue"
export { default as TagsInputItem } from "./TagsInputItem.vue"
export { default as TagsInputItemInput } from "./TagsInputItemInput.vue"
export { default as TagsInputItemText } from "./TagsInputItemText.vue"
export { default as TagsInputList } from "./TagsInputList.vue"

export const tagsInputVariants = cva(
  "flex min-h-9 w-full flex-wrap gap-1 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "border-input",
        destructive: "border-destructive focus-visible:ring-destructive",
      },
      size: {
        default: "h-9 px-3 py-1",
        sm: "h-8 px-2 py-0.5",
        lg: "h-10 px-4 py-2",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export type TagsInputVariants = VariantProps<typeof tagsInputVariants>
