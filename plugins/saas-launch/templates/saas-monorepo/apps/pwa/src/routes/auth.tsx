import { zodResolver } from "@hookform/resolvers/zod";
import { createFileRoute } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";

import { supabase } from "../lib/supabase";

export const Route = createFileRoute("/auth")({
  component: AuthPage,
});

// Local form-shape schema — deliberately NOT sourced from
// @{{PRODUCT_SLUG}}/schemas: that package models domain records (tenants,
// subscriptions, payments), not this login form's input shape.
const signInSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type SignInInput = z.infer<typeof signInSchema>;

function AuthPage() {
  const { t } = useTranslation();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<SignInInput>({ resolver: zodResolver(signInSchema) });

  const onSubmit = async (values: SignInInput) => {
    const { error } = await supabase.auth.signInWithPassword(values);
    if (error) {
      // TODO(scaffold): once @{{PRODUCT_SLUG}}/ui ships a toast/sonner
      // component (see SCAFFOLD.md §3.5), surface this there instead.
      setError("root", { message: t("auth.signInError") });
    }
  };

  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center gap-4 p-6">
      <h1 className="text-xl font-semibold">{t("auth.signIn")}</h1>
      <form className="flex flex-col gap-3" onSubmit={handleSubmit(onSubmit)} noValidate>
        <label className="flex flex-col gap-1 text-sm">
          {t("auth.email")}
          <input
            type="email"
            autoComplete="email"
            className="rounded-md border border-border bg-background px-3 py-2"
            {...register("email")}
          />
          {errors.email && <span className="text-xs text-destructive">{errors.email.message}</span>}
        </label>
        <label className="flex flex-col gap-1 text-sm">
          {t("auth.password")}
          <input
            type="password"
            autoComplete="current-password"
            className="rounded-md border border-border bg-background px-3 py-2"
            {...register("password")}
          />
          {errors.password && <span className="text-xs text-destructive">{errors.password.message}</span>}
        </label>
        {errors.root?.message && <p className="text-xs text-destructive">{errors.root.message}</p>}
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50"
        >
          {t("auth.signIn")}
        </button>
      </form>
    </main>
  );
}
