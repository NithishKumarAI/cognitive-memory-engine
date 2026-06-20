export type User = {
  id: number;
  username: string;
  email: string;
};

export type RegisterPayload = {
  username: string;
  email: string;
  password: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type AuthToken = {
  access_token: string;
  token_type: string;
};
