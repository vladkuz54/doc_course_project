"use client";

import { getMe } from "../api";
import type { ProfilePage } from "../products";
import { Messages } from "../shared/Messages";
import { useData } from "../shared/useData";

export class AdminProfilePage implements ProfilePage {
  render() {
    return <AdminProfile />;
  }
}

function AdminProfile() {
  const { data: user, error, clearMessages } = useData(getMe);

  return (
    <>
      <h1>Профіль</h1>
      <Messages error={error} onClose={clearMessages} />
      {user && (
        <dl className="details">
          <dt>Ім’я користувача</dt>
          <dd>{user.username}</dd>
          <dt>Роль</dt>
          <dd>Адміністратор</dd>
        </dl>
      )}
    </>
  );
}
