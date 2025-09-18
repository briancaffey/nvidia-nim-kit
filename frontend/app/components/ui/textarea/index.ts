import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Textarea } from "./Textarea.vue"

export const textareaVariants = cva(
  "flex min-h-[60px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "border-input",
        destructive: "border-destructive focus-visible:ring-destructive",
      },
      size: {
        default: "min-h-[60px] px-3 py-2",
        sm: "min-h-[40px] px-2 py-1",
        lg: "min-h-[80px] px-4 py-3",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export type TextareaVariants = VariantProps<typeof textareaVariants>
