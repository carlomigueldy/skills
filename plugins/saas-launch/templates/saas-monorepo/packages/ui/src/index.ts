/**
 * @{{PRODUCT_SLUG}}/ui
 *
 * Re-exports the vendored shadcn/ui components in `src/components/ui/**`
 * plus the shared `cn` classname helper (`src/lib/utils.ts`) that those
 * components import directly. See README.md for how to add or upgrade a
 * component.
 */
export { cn } from "./lib/utils";

export * from "./components/ui/badge";
export * from "./components/ui/button";
export * from "./components/ui/card";
export * from "./components/ui/dialog";
export * from "./components/ui/dropdown-menu";
export * from "./components/ui/form";
export * from "./components/ui/input";
export * from "./components/ui/label";
export * from "./components/ui/select";
export * from "./components/ui/sheet";
export * from "./components/ui/skeleton";
export * from "./components/ui/sonner";
export * from "./components/ui/table";
export * from "./components/ui/tabs";
