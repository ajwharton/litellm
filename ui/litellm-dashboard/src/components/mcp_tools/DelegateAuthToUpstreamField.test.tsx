import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { Button, Form, Input } from "antd";

import DelegateAuthToUpstreamField from "./DelegateAuthToUpstreamField";
import { AUTH_TYPE } from "./types";

const PASSTHROUGH_NOTICE = /reachable without a LiteLLM login/i;
const INTERNAL_WARNING = /Internal server with upstream OAuth delegation/i;

const Harness: React.FC<{ initialValues?: Record<string, any> }> = ({ initialValues }) => {
  const [form] = Form.useForm();
  return (
    <Form form={form} initialValues={initialValues}>
      <Form.Item name="auth_type" hidden>
        <Input />
      </Form.Item>
      <Form.Item name="available_on_public_internet" hidden>
        <Input />
      </Form.Item>
      <DelegateAuthToUpstreamField mcpServer={null} />
      <Button onClick={() => form.setFieldValue("auth_type", AUTH_TYPE.OAUTH2)}>set-oauth</Button>
      <Button onClick={() => form.setFieldValue("auth_type", "none")}>set-none</Button>
    </Form>
  );
};

const renderField = (initialValues: Record<string, any> = {}) => render(<Harness initialValues={initialValues} />);

const selectOAuth = async (user: ReturnType<typeof userEvent.setup>) =>
  user.click(screen.getByRole("button", { name: "set-oauth" }));

describe("DelegateAuthToUpstreamField", () => {
  it("renders nothing when auth_type is not oauth2", () => {
    renderField({ auth_type: "bearer_token" });
    expect(screen.queryByRole("switch")).not.toBeInTheDocument();
    expect(screen.queryByText(/delegate auth to upstream/i)).not.toBeInTheDocument();
  });

  it("shows the toggle but hides the passthrough notice while delegation is off", async () => {
    const user = userEvent.setup();
    renderField();
    await selectOAuth(user);

    expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "false");
    expect(screen.queryByText(PASSTHROUGH_NOTICE)).not.toBeInTheDocument();
  });

  it("shows the passthrough notice once delegation is enabled", async () => {
    const user = userEvent.setup();
    renderField({ available_on_public_internet: true });
    await selectOAuth(user);

    expect(screen.queryByText(PASSTHROUGH_NOTICE)).not.toBeInTheDocument();
    await user.click(screen.getByRole("switch"));

    expect(screen.getByText(PASSTHROUGH_NOTICE)).toBeInTheDocument();
    expect(screen.queryByText(INTERNAL_WARNING)).not.toBeInTheDocument();
  });

  it("warns when delegation is on for an internal-only server", async () => {
    const user = userEvent.setup();
    renderField({ available_on_public_internet: false });
    await selectOAuth(user);
    await user.click(screen.getByRole("switch"));

    expect(screen.getByText(PASSTHROUGH_NOTICE)).toBeInTheDocument();
    expect(screen.getByText(INTERNAL_WARNING)).toBeInTheDocument();
  });

  it("resets delegation to false when auth_type leaves oauth2", async () => {
    const user = userEvent.setup();
    renderField();
    await selectOAuth(user);
    await user.click(screen.getByRole("switch"));
    expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "true");

    await user.click(screen.getByRole("button", { name: "set-none" }));
    expect(screen.queryByRole("switch")).not.toBeInTheDocument();

    await selectOAuth(user);
    expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "false");
  });
});
