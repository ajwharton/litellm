import React, { useEffect } from "react";
import { Alert, Form, Switch, Tooltip } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import { MCPServer, AUTH_TYPE } from "./types";

interface DelegateAuthToUpstreamFieldProps {
  mcpServer: MCPServer | null;
}

const DelegateAuthToUpstreamField: React.FC<DelegateAuthToUpstreamFieldProps> = ({ mcpServer }) => {
  const form = Form.useFormInstance();
  const authType = Form.useWatch("auth_type", form);
  const isOAuth2 = authType === AUTH_TYPE.OAUTH2;
  const delegateAuth = Form.useWatch("delegate_auth_to_upstream", form) === true;
  const internalOnly = Form.useWatch("available_on_public_internet", form) === false;

  // delegate_auth_to_upstream is only honored server-side when auth_type=oauth2.
  // Force it back to false whenever the user switches away from oauth2 so a stale
  // toggle value doesn't get persisted with another auth type. Guard on a defined
  // auth_type so the initial undefined render doesn't clobber a saved value.
  useEffect(() => {
    if (authType !== undefined && !isOAuth2) {
      form.setFieldValue("delegate_auth_to_upstream", false);
    }
  }, [authType, isOAuth2, form]);

  if (!isOAuth2) return null;

  return (
    <div className="space-y-3 mb-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="text-sm font-medium text-gray-700 flex items-center">
            Delegate auth to upstream (PKCE passthrough)
            <Tooltip title="When on, LiteLLM skips its own API key/SSO check for this server and lets the client complete PKCE directly with the upstream MCP server. Only honored when Auth Type is oauth2. No spend tracking or per-key rate limiting will run on this route.">
              <InfoCircleOutlined className="ml-2 text-blue-400 hover:text-blue-600 cursor-help" />
            </Tooltip>
          </span>
          <p className="text-sm text-gray-600 mt-1">
            Bypass LiteLLM auth so clients authenticate directly with the upstream OAuth MCP server.
          </p>
        </div>
        <Form.Item
          name="delegate_auth_to_upstream"
          valuePropName="checked"
          initialValue={mcpServer?.delegate_auth_to_upstream ?? false}
          className="mb-0"
        >
          <Switch />
        </Form.Item>
      </div>

      {delegateAuth && (
        <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700 flex items-start gap-2">
          <InfoCircleOutlined className="mt-0.5 flex-shrink-0" />
          <span>
            Clients authenticate directly with the upstream MCP server. LiteLLM won&apos;t require its own API key/SSO
            on this route and won&apos;t store user credentials, so this endpoint is reachable without a LiteLLM login.
          </span>
        </div>
      )}

      {delegateAuth && internalOnly && (
        <Alert
          type="warning"
          showIcon
          message="Internal server with upstream OAuth delegation"
          description="This MCP server is configured as internal-only but delegates auth to upstream. Anonymous users will be able to reach the upstream OAuth2 /authorize flow without a LiteLLM session. Ensure your upstream provider and network enforce access controls."
        />
      )}
    </div>
  );
};

export default DelegateAuthToUpstreamField;
