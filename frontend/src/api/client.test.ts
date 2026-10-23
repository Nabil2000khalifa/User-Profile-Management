import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "./client";

describe("api client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    Object.defineProperty(document, "cookie", { configurable: true, value: "admin_csrf=test-csrf" });
  });

  it("sends credentials and CSRF headers for profile creation", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ id: 1 }), { status: 201 }));
    await api.createProfile({ first_name: "A", last_name: "B", date_of_birth: "1990-01-01", email: "a@example.com", country: "US", city: "Chicago" });
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/v1/profiles", expect.objectContaining({
      credentials: "include",
      headers: expect.any(Headers),
    }));
    const options = fetchMock.mock.calls[0][1] as RequestInit;
    expect((options.headers as Headers).get("X-CSRF-Token")).toBe("test-csrf");
  });

  it("maps backend field errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: [{ loc: ["body", "email"], msg: "Already exists" }] }), { status: 409 }));
    await expect(api.createProfile({ first_name: "A", last_name: "B", date_of_birth: "1990-01-01", email: "a@example.com", country: "US", city: "Chicago" })).rejects.toMatchObject({ status: 409, fieldErrors: { email: "Already exists" } });
  });
});
