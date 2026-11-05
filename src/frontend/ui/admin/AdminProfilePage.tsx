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
      <h1>Profile</h1>
      <Messages error={error} onClose={clearMessages} />
      {user && (
        <dl className="details">
          <dt>Username</dt>
          <dd>{user.username}</dd>
          <dt>Role</dt>
          <dd>Administrator</dd>
        </dl>
      )}
    </>
  );
}
