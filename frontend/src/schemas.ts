import { z } from "zod";

export const loginSchema = z.object({
  email: z.email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

export const profileSchema = z.object({
  first_name: z.string().trim().min(1, "First name is required.").max(100),
  last_name: z.string().trim().min(1, "Last name is required.").max(100),
  date_of_birth: z
    .string()
    .min(1, "Date of birth is required.")
    .refine((value) => value >= "1900-01-01", "Date of birth must be on or after January 1, 1900."),
  email: z.email("Enter a valid email address."),
  country: z.string().min(1, "Country is required."),
  city: z.string().min(1, "City is required."),
});

export type LoginValues = z.infer<typeof loginSchema>;
export type ProfileValues = z.infer<typeof profileSchema>;
