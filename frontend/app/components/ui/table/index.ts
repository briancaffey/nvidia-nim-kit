import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Table } from "./Table.vue"
export { default as TableBody } from "./TableBody.vue"
export { default as TableCaption } from "./TableCaption.vue"
export { default as TableCell } from "./TableCell.vue"
export { default as TableHead } from "./TableHead.vue"
export { default as TableHeader } from "./TableHeader.vue"
export { default as TableRow } from "./TableRow.vue"

export const tableVariants = cva(
  "w-full caption-bottom text-sm",
  {
    variants: {
      variant: {
        default: "border-collapse",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
)

export type TableVariants = VariantProps<typeof tableVariants>
