import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";
import { profileSchema } from "./schemas";

vi.mock("./auth", () => ({
  useAuth: () => ({ admin: null, loading: false, error: null, login: vi.fn(), logout: vi.fn() }),
}));

describe("App", () => {
  it("renders the admin login", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Welcome back" })).toBeTruthy();
    expect(screen.getByLabelText("Admin email")).toBeTruthy();
    expect(screen.getByLabelText("Password")).toBeTruthy();
  });

  it("shows accessible login validation errors before making a request", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Sign in securely" }));

    await waitFor(() => {
      expect(screen.getByText("Enter a valid email address.")).toBeTruthy();
      expect(screen.getByText("Enter your password.")).toBeTruthy();
    });
  });

  it("rejects dates of birth before the supported minimum", () => {
    const result = profileSchema.safeParse({
      first_name: "John",
      last_name: "Doe",
      date_of_birth: "0001-01-01",
      email: "john@example.com",
      country: "US",
      city: "Chicago",
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0]?.message).toContain("1900");
    }
  });
});
