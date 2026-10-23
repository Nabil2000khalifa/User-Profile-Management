export type Admin = { id: number; email: string };
export type LoginResponse = { admin: Admin; csrf_token: string };
export type Profile = {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  email: string;
  country: string;
  city: string;
  created_at: string;
  updated_at: string;
};
export type ProfilePage = {
  items: Profile[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};
export type ProfilePayload = Omit<
  Pick<Profile, "first_name" | "last_name" | "date_of_birth" | "email" | "country" | "city">,
  never
>;
export type CountryResponse = { items: string[] };
export type CityResponse = { items: string[] };
